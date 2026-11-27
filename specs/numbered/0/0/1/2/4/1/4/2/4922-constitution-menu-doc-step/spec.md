# Feature Specification: Menu step names the generated pages

**Feature Branch**: `docs/4922-constitution-menu-doc-step`

**Created**: 2026-11-26

**Status**: Draft

**Input**: GitHub issue #4922, "Docs: the constitution step for a new menu operation still asks for a README table".

## Clarifications

### Session 2026-11-26

- Q: Which README statements change? A: Step 5 of "Adding New Menu Operations" and the README bullet of the Documentation section in `.specify/memory/constitution.md`. Issue #4916 removed the menu content from the README, so both statements are stale.
- Q: Does the agent rule file change in the same pull request? A: Yes. Step 1 of "Add a menu operation" in `.github/copilot-instructions.md` still names the README menu table on `main`. This change corrects that step, so both files give one rule.
- Q: Where do the guard cases go? A: In the existing class `TestPolicyStaysStated` in `tests/guardrails/test_changelog_fragment_policy.py`. The `tests/guardrails` folder holds 79 direct children on `main`, so it breaks the Five-Item Rule. No new file goes there.
- Q: Which version bump applies? A: PATCH, from 1.9.0 to 1.9.1. The amendment corrects wording and adds no principle.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Menu step names the generated pages (Priority: P1)

A maintainer adds a menu operation and reads step 5 of "Adding New Menu Operations". Step 5 names the generator command, the two generated pages, and the operator guide. Step 5 names no README menu table.

**Why this priority**: The stale step sends each maintainer to a README table that issue #4916 removed. Each new menu operation repeats the error.

**Independent Test**: Read step 5 in `.specify/memory/constitution.md`. Run the guard case `menu-step` in `tests/guardrails/test_changelog_fragment_policy.py`.

**Acceptance Scenarios**:

1. **Given** the amended constitution, **When** a maintainer reads step 5, **Then** the step names `scripts/generate_menu_wiki.py`, `documentation/menu_reference.md`, `documentation/wiki/Menu-Reference.md`, and `documentation/operator-guide.md`.
2. **Given** the amended constitution, **When** a maintainer searches step 5 for "menu table", **Then** the search returns no match.

---

### User Story 2 - README and rule file give one rule (Priority: P1)

An agent reads step 1 of "Add a menu operation" in `.github/copilot-instructions.md`. A maintainer reads the README bullet in the constitution. Both sources state that the README holds no menu number and no per-operation text.

**Why this priority**: The rule file is the first file that an agent reads. A stale step there gives the agent the old instruction.

**Independent Test**: Run the guard cases `readme-bullet` and `rule-file-step`.

**Acceptance Scenarios**:

1. **Given** the amended constitution, **When** a reader checks the README bullet, **Then** the bullet states that the README holds no menu number or per-operation text.
2. **Given** the amended rule file, **When** an agent reads step 1 of "Add a menu operation", **Then** the step names `documentation/operator-guide.md` and no README table.

---

### User Story 3 - Governance record shows the amendment (Priority: P2)

A reviewer reads the constitution footer and the Sync Impact Report. Both show version 1.9.1, a PATCH amendment, and the amendment date 2026-11-26. The release-note step and the WebSocket exception stay unchanged.

**Why this priority**: The constitution governs each change. Its version and report must record the amendment that it contains.

**Independent Test**: Run the guard cases `footer-version` and `sync-report`. Run `tests/guardrails/test_websocket_transport_constitution.py`.

**Acceptance Scenarios**:

1. **Given** the amended constitution, **When** a reviewer reads the footer, **Then** the footer shows `**Version**: 1.9.1` and `**Last Amended**: 2026-11-26`.
2. **Given** the amended constitution, **When** a reviewer reads the Sync Impact Report, **Then** the report shows `1.9.0 -> 1.9.1 (PATCH)`.

---

### Edge Cases

- A new menu operation needs no operator note. Step 5 requires a note only when the operation needs operator steps.
- A destructive operation needs operator steps. The operator guide already states the confirmation words for menus 164, 305, and 306 in `documentation/operator-guide.md`, lines 118 to 130.
- A new operation is added without regenerating the pages. The `menu_reference_drift` job in `.github/workflows/ci.yml` fails. Step 5 requires regeneration before the commit.
- A historical spec record quotes the old step. The record stays unchanged, because it documents past work. Decision D-8 applies.
- The pull request opens after the fragment is written. The fragment keeps its issue-form name, because `changelog.d/README.md` says to keep the first name.
- A reader expects every behavior change to update the README. The amended bullet removes that duty. Operator details live in `documentation/operator-guide.md`.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Step 5 of "Adding New Menu Operations" in `.specify/memory/constitution.md` MUST name `scripts/generate_menu_wiki.py`, `documentation/menu_reference.md`, `documentation/wiki/Menu-Reference.md`, and `documentation/operator-guide.md`.
- **FR-002**: Step 5 MUST NOT name the README menu table, the operation count, or the phrase "Update README".
- **FR-003**: The README bullet in the Documentation section MUST state that the README holds no menu number and no per-operation text. The bullet MUST name `documentation/operator-guide.md`.
- **FR-004**: Step 1 of "Add a menu operation" in `.github/copilot-instructions.md` MUST name `documentation/operator-guide.md`. The step MUST NOT name the README menu table.
- **FR-005**: The constitution footer MUST show version 1.9.1 and Last Amended 2026-11-26.
- **FR-006**: The Sync Impact Report MUST record the amendment as `1.9.0 -> 1.9.1 (PATCH)`.
- **FR-007**: The release-note step 6 and its fragment name forms MUST remain unchanged. The existing class `TestPolicyStaysStated` MUST pass.
- **FR-008**: The change MUST add the fragment `changelog.d/issue-4922-constitution-menu-doc-step.md`. The fragment MUST hold one `###` heading and one `Changed` bullet that names issue 4922.
- **FR-009**: All new and changed prose MUST follow the Simplified Technical English rules in `AGENTS.md`. The `ste-linter` gate MUST score `.github/copilot-instructions.md` at 80 or above.
- **FR-010**: The WebSocket exception text in the constitution MUST remain unchanged. The guard `tests/guardrails/test_websocket_transport_constitution.py` MUST pass.

### Key Entities

None. This change stores no data and defines no entity.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The constitution contains no "menu table" text, no "Update README" text, and no "operation count" text after the change.
- **SC-002**: The rule file contains no "menu table in `README.md`" text after the change.
- **SC-003**: All five new guard cases fail on the unchanged text, and all five pass after the change.
- **SC-004**: The guard tests in `tests/guardrails/test_changelog_fragment_policy.py` and `tests/guardrails/test_websocket_transport_constitution.py` pass.
- **SC-005**: The `ste-linter` gate scores `.github/copilot-instructions.md` at 80 or above. The measured score of `.specify/memory/constitution.md` appears in the pull request body.
- **SC-006**: The implementation diff changes exactly the four files in the file map of `plan.md`, and it adds the record folder.
- **SC-007**: Each required check on the pull request passes before anyone adds the `auto-merge` label.

## Assumptions

- The owner decision of issue #4916 stays in force. The README holds no menu content.
- The generated pages stay the source of the menu list. `scripts/generate_menu_wiki.py` writes both generated pages.
- The operator guide stays the page for operator details.
- The amendment date is 2026-11-26.
- The change edits Markdown and one guard test module. It changes no runtime code.

## Out of Scope

- The stale operation count in `documentation/operator-guide.md`. Issue #4915 tracks it.
- Historical spec records that quote the old step, such as `specs/3560-wan-edge-scorecard/wiring.md`.
- The README content. Issue #4916 covered that work.
- The list of STE files in `.github/workflows/ste-lint.yml`. A separate issue decides that list.
- The generic README checkbox in `.github/PULL_REQUEST_TEMPLATE.md`, line 35.
- The templates in `.specify/templates/`.
- The conflict between constitution step 6 and rule 4 of `changelog.d/README.md`. `analysis.md` records it.
