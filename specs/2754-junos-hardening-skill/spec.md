# Feature Specification: Junos hardening skill

**Feature Branch**: `docs/2754-junos-hardening-skill`

**Created**: 2026-09-16

**Status**: Draft

**Input**: GitHub issue #2754 asks for a source-grounded `hardening-junos` skill.

## Finding

No Junos hardening skill exists in the current repository skill folder or in the
current session skill list. The repository does contain security rules that the
new skill must cite. This feature adds one new skill instead of creating a
second term for an existing concept.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Answer a MistHelper Junos hardening question (Priority: P1)

A junior NOC engineer asks how to handle a Junos security decision that
MistHelper can touch. The agent answers with repository evidence and a Junos
source.

**Why this priority**: This gives the operator safe guidance for the highest
risk questions.

**Independent Test**: Ask about a ZTP password or zeroize command. The answer
must cite repository and Juniper sources.

**Acceptance Scenarios**:

1. **Given** a ZTP password question, **When** the skill runs, **Then** it tells
the agent not to log the credential.
2. **Given** a zeroize question, **When** the skill runs, **Then** it requires a
recovery plan and typed confirmation.

---

### User Story 2 - Select the correct source (Priority: P2)

A maintainer updates the skill or reviews a hardening answer. The maintainer can
find the source hierarchy and the indexed source list.

**Why this priority**: Source routing stops generic hardening advice from
entering the repository.

**Independent Test**: Read the source index. Each indexed source must have a
title, train or version, and path or URL.

**Acceptance Scenarios**:

1. **Given** a repository claim, **When** a maintainer checks the source index,
**Then** the index points to a repository file.
2. **Given** a Junos claim, **When** a maintainer checks the source index,
**Then** the index points to a Juniper source.

---

### User Story 3 - Preserve known gaps (Priority: P3)

A maintainer can see which corpus claims were not verified in the current
worktree.

**Why this priority**: A visible gap is safer than an unstated assumption.

**Independent Test**: Read the validation and gaps reference. It must list six
unverified PDF gaps from issue #2754.

**Acceptance Scenarios**:

1. **Given** the external corpus is absent, **When** a maintainer reads the gap
register, **Then** each missing PDF is marked unverified.

### Edge Cases

- If a source is absent, the skill must mark the claim unverified.
- If a user asks for generic Junos hardening, the skill must narrow the answer
to MistHelper contact points.
- If a command can erase data, the skill must classify it as destructive.
- If an example needs a secret, the skill must use an obvious placeholder.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST add one `hardening-junos` skill under
`.github/skills/`.
- **FR-002**: The skill MUST state that its scope is MistHelper contact points
with Junos devices.
- **FR-003**: The skill MUST exclude generic Junos hardening that has no
MistHelper path.
- **FR-004**: The skill MUST define a source hierarchy for repository and Junos
claims.
- **FR-005**: The skill MUST include a source index with title, train or version,
and path or URL.
- **FR-006**: The skill MUST teach the repository rules for secrets, `.env`,
typed confirmation, ASCII logs, and security findings.
- **FR-007**: The skill MUST include the ZTP password terminal-gate decision.
- **FR-008**: The skill MUST include the destructive operation set and human
review rule.
- **FR-009**: The skill MUST cite repository file and line evidence for
repository claims.
- **FR-010**: The skill MUST cite Juniper documentation for Junos command claims.
- **FR-011**: The skill MUST mark missing corpus details as unverified.
- **FR-012**: The skill directory MUST stay at or below 400 KB.
- **FR-013**: The skill Markdown MUST score 80 or above on the STE linter.

### Key Entities

- **Skill entry point**: The `SKILL.md` file that the agent host discovers.
- **Source index**: A table that maps each source to title, train or version,
and path or URL.
- **Repository decision**: A MistHelper security rule with file and line
evidence.
- **Junos rule**: A Junos command or statement claim with a vendor source.
- **Gap register**: A list of missing source items that remain unverified.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The skill package is 400 KB or smaller.
- **SC-002**: Each repository rule in the skill has a file and line citation.
- **SC-003**: Each Junos command or statement claim has a Juniper citation.
- **SC-004**: Each Markdown file added by this feature scores 80 or above with
the STE linter.
- **SC-005**: The local gates named in issue #2754 run, or the report records the
exact blocker.

## Assumptions

- The external Juniper corpus is not present in the `origin/main` worktree.
- The skill can cite public Juniper documentation for verified Junos claims.
- Missing corpus PDF names must remain visible as unverified gaps.
- This is a documentation-only change.
