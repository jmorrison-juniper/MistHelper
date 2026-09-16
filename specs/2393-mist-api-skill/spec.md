# Feature Specification: Source-grounded Mist API skill

**Feature Branch**: `docs/2393-mist-api-skill`

**Created**: 2026-09-16

**Status**: Draft

**Input**: GitHub issue #2393 asks for a repository skill for source-grounded Mist API work.

## User Scenarios and Testing

### User Story 1 - Answer with local source evidence (Priority: P1)

A junior NOC engineer asks how to use a Mist API operation.
The skill directs the engineer to the installed SDK, the OpenAPI source, and the endpoint page.

**Why this priority**: This prevents an answer that uses a stale endpoint or a guessed schema.

**Independent Test**: Read the skill entry point and confirm that it names the source hierarchy.

**Acceptance Scenarios**:

1. **Given** an API question, **When** the agent opens the skill, **Then** it reads the source hierarchy before it answers.
2. **Given** an SDK call, **When** the agent writes Python, **Then** it verifies the installed function and signature first.

---

### User Story 2 - Resolve source conflicts safely (Priority: P2)

A maintainer sees a difference between the bundled OpenAPI source and the installed SDK.
The skill states which source wins for a call signature, a schema, and MistHelper support.

**Why this priority**: A stale SDK path can fail on production hardware.

**Independent Test**: Read `references/source-authority.md` and confirm the conflict rules.

**Acceptance Scenarios**:

1. **Given** the `aos` to `aoscx` rename, **When** the agent writes a call, **Then** it uses the installed SDK path.
2. **Given** a missing `getSite` call, **When** the agent checks the SDK, **Then** it rejects the missing function.

---

### User Story 3 - Bound live Mist work (Priority: P3)

An operator asks for a live Mist API request.
The skill requires the agent to confirm host, scope, safety class, pagination, and completion evidence.

**Why this priority**: A token does not approve a configuration change.

**Independent Test**: Read the request lifecycle guide and confirm that it separates read-only, diagnostic, and destructive work.

**Acceptance Scenarios**:

1. **Given** a destructive operation, **When** the agent plans a request, **Then** it obtains explicit confirmation before execution.
2. **Given** a paged export, **When** the agent collects data, **Then** it reports incomplete pages separately from empty results.

### Edge Cases

- If the installed SDK and OpenAPI source disagree, the skill must name the conflict and stop unsafe execution.
- If an endpoint page contains generated notes, the agent must verify each material note against the source.
- If a live request needs a credential, the agent must not print or store the credential.
- If a MistHelper menu number changes, the agent must read the operation registry before it states support.

## Requirements

### Functional Requirements

- **FR-001**: The skill MUST name the installed `mistapi` package as the source for SDK call signatures.
- **FR-002**: The skill MUST name the OpenAPI 3.1 JSON and YAML files as the source for HTTP paths and schemas.
- **FR-003**: The skill MUST route readers to `documentation/api/INDEX.md` and endpoint pages for discovery.
- **FR-004**: The skill MUST route MistHelper support claims to `src/export/endpoint_catalog.py` and `src/utils/operation_registry.py`.
- **FR-005**: The skill MUST warn that generated notes and saved examples require verification.
- **FR-006**: The skill MUST state that no live Mist request occurs for documentation or code examples.
- **FR-007**: The skill MUST warn about stale SDK calls such as `getSite` and `listSites`.
- **FR-008**: The skill MUST require source evidence for each endpoint, schema, and SDK path that it states.

### Key Entities

- **Skill entry point**: The file that activates the Mist API guidance.
- **Reference guide**: A skill document that explains one source-grounded workflow.
- **Operation contract**: The method, path, parameters, schema, SDK callable, source, and safety class for one API operation.

## Success Criteria

### Measurable Outcomes

- **SC-001**: The repository contains exactly one Mist API skill.
- **SC-002**: The skill identifies the current OpenAPI version `2607.1.1` and 756 paths.
- **SC-003**: The skill records how to verify SDK functions before implementation.
- **SC-004**: The STE linter scores every written Markdown file at 80 or higher.
- **SC-005**: Local validation gates complete or report a clear blocker.

## Assumptions

- The repository worktree for issue #2393 is the correct worktree to continue.
- The user profile skill and the repository skill serve the same concept.
- The correct action is to improve the repository skill, not to add a second Mist API skill.
- The change is documentation-only and does not require a live Mist API request.
