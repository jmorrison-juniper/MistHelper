# Feature Specification: Converter Privacy and Shared Portal Integration

**Feature Branch**: `feat/4648-converter-portal-integration`

**Created**: 2026-11-26

**Status**: Draft

**Issue**: #4648, "[Spec]: Verify converter privacy and integrate with the shared portal"

**Parent**: #4224. **Task map**: PR #4596, `specs/live/0/0/0/1/2/1/3/3/2/1/4/2/1/4/1/3/0/20261105-170040-cisco-converter-full-parity/`. This record covers tasks T031 and T032 of that map.

**Input**: GitHub issue #4648. The issue asks for cross-cutting privacy, security, and regression tests. It then asks for a G3-gated integration into the shared portal.

## Terms

Each term keeps one meaning in this record.

- **Converter**: The Cisco IOS config converter in `src/interfaces/portals/cisco_config_converter/`.
- **Portal**: The MistHelper web portal that `WebPortalApp.create_app` builds.
- **Shared portal files**: `web_portal/app.py` and `web_portal/templates/base.html`.
- **G3 handover**: The written owner decision that allows one change to the shared portal files.
- **Composition harness**: A test-only fixture that adds the converter to a real portal app in memory.
- **Local gate**: A command from the local gates table in `.github/copilot-instructions.md`.
- **Remote check**: One comparison of a path with GitHub `main` by blob or tree SHA.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Prove privacy and safety before integration (Priority: P1)

An engineer runs the cross-cutting tests before any shared portal file changes. The tests use the real portal factory, synthetic input, and mocked responses.

**Why this priority**: The issue requires cross-cutting tests before integration. These tests protect existing portal behavior from regression.

**Independent Test**: Run `python -m pytest tests/integration/web_portal/cisco_config_converter/test_parity.py`. The suite passes with no live network call and no shared-file change.

**Acceptance Scenarios**:

1. **Given** the portal has no converter registration, **When** the composition harness adds the converter, **Then** `/health` and `/ready` keep their status codes and JSON keys.
2. **Given** a converter POST without a valid CSRF token, **When** the request reaches the portal, **Then** the answer has status 400 and holds no traceback.
3. **Given** a converter upload with synthetic secret and source text, **When** the operator previews, reviews, and exports, **Then** logs and session hold neither value.

---

### User Story 2 - Integrate the converter into the real portal after G3 handover (Priority: P1)

After the G3 handover and the prerequisite issues close, the portal shows one converter entry. The converter routes run from the real portal factory.

**Why this priority**: Operators cannot use the converter until the portal shows it.

**Independent Test**: Run `python -m pytest tests/integration/web_portal/cisco_config_converter/test_portal_browser.py`. The browser opens the converter from the navigation bar and completes preview, review, and export.

**Acceptance Scenarios**:

1. **Given** the G3 handover is recorded, **When** the portal starts, **Then** the navigation bar holds one entry with `data-testid="nav-cisco-converter"`.
2. **Given** a browser session on the portal, **When** the operator completes preview, review, and export, **Then** the downloaded JSON equals the reviewed proposal.
3. **Given** a browser test fails, **When** pytest ends the test, **Then** a screenshot exists under `test-artifacts/cisco-portal/`.

---

### User Story 3 - Keep cloud writes disabled and portal behavior unchanged (Priority: P2)

The portal keeps its existing routes, health reply, and service ownership. The converter exposes only approved routes and no cloud write route.

**Why this priority**: A cloud write changes production state. This issue grants no write authorization.

**Independent Test**: Run the route allowlist and Compose tests in `test_parity.py`. Both pass with the approved route set.

**Acceptance Scenarios**:

1. **Given** the converter blueprint, **When** the route table is read, **Then** only the approved converter routes exist.
2. **Given** `compose.yml`, **When** its services are read, **Then** no converter service exists.

---

### Edge Cases

- PR #4208 stays open. Then T009 and T010 stay blocked, and T002 through T008 continue.
- A new converter route appears. Then the route allowlist test fails until owner approval.
- A converter request has no trailing slash. Then the portal redirects it before it parses the body.
- A JSON client and an HTML client send the same invalid token. Then each client receives its own answer shape, both with status 400.
- Two portal processes start with different random secrets. Then CSRF fails across the processes. Tests use one synthetic key. Production policy stays open under D-9.
- A comparison row changes state in another issue. Then the matrix guard fails until this record changes the row.
- The E2E timeout hook does not cover the browser module. Then the module sets its own timeout mark of 120 seconds.

### Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The integration MUST keep existing portal routes, health, authentication, service ownership, and data behavior unchanged.
- **FR-002**: Tests MUST prove that `/health` and `/ready` keep their status codes and JSON keys.
- **FR-003**: Tests MUST prove that a converter POST without a valid CSRF token returns a safe 400 answer.
- **FR-004**: Tests MUST prove that converter errors follow the shared CSRF answer shape for JSON and HTML callers.
- **FR-005**: Tests MUST prove that converter error bodies hold no traceback and no source text.
- **FR-006**: Tests MUST prove that Flask debug mode stays off in the portal and the container path.
- **FR-007**: Tests MUST prove that converter logs hold no source text, file name, template name, or secret value.
- **FR-008**: Tests MUST prove that the converter path opens no network connection and imports no network module.
- **FR-009**: Every comparison row C01 through C40 MUST have a disposition and at least one linked test or remaining task.
- **FR-010**: Tests MUST use synthetic input, mocked responses, and no live credential.
- **FR-011**: The integration MUST NOT change a shared portal file before the G3 handover is recorded.
- **FR-012**: After the G3 handover, the real portal factory MUST register the converter blueprint and its request class.
- **FR-013**: After the G3 handover, the navigation bar MUST hold one converter entry with a stable test identifier.
- **FR-014**: Browser tests MUST run the converter journey through the real portal with the existing Playwright setup.
- **FR-015**: Existing portal regression suites MUST pass after the integration.
- **FR-016**: The converter MUST expose only approved routes, and no cloud write route MUST exist.
- **FR-017**: The integration MUST NOT add a database, Redis service, Compose service, or credential source.
- **FR-018**: Each new directory MUST hold five children or fewer, and no new direct child MUST enter a noncompliant parent.
- **FR-019**: The integration MUST update the operator guide and add one changelog fragment.
- **FR-020**: Browser evidence MUST go to the git-ignored `test-artifacts/` folder.

### Mist Cloud Transport Requirements *(include if feature uses Mist Cloud)*

Not applicable. This integration makes no Mist REST or WebSocket request. Remote checks R-07 and R-42 show that the converter imports no SDK module and that Compose holds no converter service.

### Key Entities *(include if feature involves data)*

Entities, keys, and state transitions appear in `design/data-model.md`.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The offline suite passes with zero live network calls. Pytest reports the case count.
- **SC-002**: Before the G3 handover, `git diff` shows no change in `web_portal/app.py` or `web_portal/templates/base.html`.
- **SC-003**: After the G3 handover, `/health` and `/ready` match the baseline status codes and JSON keys.
- **SC-004**: Each browser test failure writes a screenshot under `test-artifacts/cisco-portal/`.
- **SC-005**: Each comparison row C01 through C40 has one disposition and at least one linked test or task.
- **SC-006**: No log line in the test run holds the synthetic source text or the synthetic secret.
- **SC-007**: The existing portal regression suites report the same pass count before and after the integration.
- **SC-008**: The converter route set equals the approved set, and it holds zero cloud write routes.

## Assumptions

- The coordinator account `jmorrison-juniper` owns the integration change. Source: issue #4633, comment of 2026-11-08T23:37:56Z.
- PR #4208 owns both shared portal files until it closes or merges. It was OPEN on 2026-11-26.
- The container runs one Gunicorn worker. Source: `wsgi.py` line 4.
- Flask 3.1.3 and Flask-WTF 1.3.0 stay pinned. Source: `requirements.txt` lines 49 and 54.
- The browser setup uses `pytest-playwright` 0.10.0. Source: `requirements-dev.txt` line 333.
- The converter stays offline. No task adds a Mist call.

## Out of Scope

- Conversion rules and mapping changes (issues #4637 through #4640).
- Proposal format changes (issue #4641).
- Private backups and the storage policy (issue #4643).
- Gated apply (issue #4644) and reviewed recovery (issue #4646).
- Visual journeys and themes (issue #4647).
- Legal review and the license basis (issue #4635).
- Mist API contract verification (issue #4634).
- Live Mist tests and any production operation.

## Clarifications

### Session 2026-11-26

- Q: Is implementation authorized? A: Offline implementation and synthetic tests are authorized. Shared-file changes need the G3 handover. Source: issue #4633, comment of 2026-11-08T23:37:56Z.
- Q: Who owns the later integration change? A: Account `jmorrison-juniper`. Source: the same issue #4633 comment.
- Q: Which PRs own the shared files? A: PR #4208 owns both files and is OPEN. PR #4615 merged on 2026-11-13 and no longer blocks.
- Q: May a test use live Mist credentials? A: No. Live tests run only in the NVMM lab under decision gate G5. This issue starts none.
- Q: Does the integration add a route? A: No. It registers the existing converter blueprint only.
