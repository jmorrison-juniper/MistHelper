# Feature Specification: Sign-in credential layout

**Feature Branch**: `jmorrison-juniper-sign-in-credential-layout`
**Created**: 2026-10-02
**Status**: Implementation
**Input**: Repair [issue #3295](https://github.com/jmorrison-juniper/MistHelper/issues/3295) without changing authentication policy.
**Recorded Base**: `5d38898af5639e90715ec57eb8d48d2985e1acf8`

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Read the token group correctly (Priority: P1)

An operator selects browser-token mode. The token label sits directly above its masked field.
The note and field form one semantic group below the credential mode buttons.

**Why this priority**: The previous label occupied the empty space beside the mode buttons.

**Independent Test**: Measure the shipped sign-in page at 1280x720 and 360x800 CSS pixels.
Use the actual native upgrade themes, `magenta` and `default`.

**Acceptance Scenarios**:

1. The label and field left edges differ by at most 1 CSS pixel.
   The label bottom does not exceed the field top. Their vertical gap is 0 through 16 CSS pixels.

2. The complete token group sits below every mode button.
   Its label, field, and note stay inside the group and viewport.

3. The native label association names the field `Mist API token`.
   A label click focuses that field.

### User Story 2 - Change modes without losing inputs (Priority: P1)

An operator changes credential modes. The unused token cannot receive keyboard focus or enter native form data.

**Why this priority**: The previous provider mode exposed an active token field that it did not use.

**Independent Test**: Drive the real controller and browser with synthetic values and controlled dependencies.

**Acceptance Scenarios**:

1. Provider mode hides the token field and note. It disables the field and excludes it from successful form controls.

2. Browser-token mode restores the field, note, and native keyboard reach.
   Tab reaches the field after the selected radio. Shift+Tab returns from Sign in.

3. Mode changes preserve the token, email, password, and selected cloud.
   They restore the original provider requirements without adding listeners or requests.

4. After ten complete switch cycles, one nonempty token submission creates exactly one JSON request.
   The script clears the token before the request and keeps it empty after refusal.

5. Empty and whitespace-only client tokens create zero requests and retain the current client cure.

6. An environment-token startup retains its existing mode and optional password baseline.
   It renders no browser-token choice, group, or field.

### User Story 3 - Read a consistent warning (Priority: P2)

An operator reads a service warning, sign-in refusal, or actual error page.
Each danger alert starts with the same bold `Warning:` prefix.

**Why this priority**: The previous sign-in prefix had weight 400. The error-page prefix had weight 700.

**Independent Test**: Measure each generated prefix on real local route responses.

**Acceptance Scenarios**:

1. Each visible danger prefix uses weight 700 and exact generated text `"Warning: "`.

2. Empty alerts remain hidden and expose no bare signal word.

3. Refusal wording, plain-text display, template escaping, colors, and adjacent signal words remain unchanged.

### Edge Cases

- Mode buttons wrap on the narrow viewport. The token group remains below the last button.
- A token survives a mode change in browser memory. A disabled field does not enter a provider submission.

- Missing token structure leaves initialization harmless without a compatibility fallback.
- An invalid provider input keeps native validation active and creates no request.

- Missing Playwright uses the repository's ordinary module skip and strict failure behavior.
- The service table already extends the 360-pixel page to a 400-pixel scroll width.
  Preserve that unrelated overflow outside the token group.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Use one named semantic group for the token label, field, and note outside the flex mode fieldset.
- **FR-002**: Meet the exact geometry limits in User Story 1. Add stable group and label identifiers.
- **FR-003**: Hide and disable the token outside browser-token mode. Restore native keyboard reach inside that mode.

- **FR-004**: Preserve entered values and original provider validation. Add no mode-change listener or credential reset.
- **FR-005**: Preserve startup gating, literal mode values, native CSRF, JSON-only token transport, and clear-before-request behavior.
- **FR-006**: Preserve all existing server decisions, destinations, statuses, session rules, and #3290 refusal messages.

- **FR-007**: Reuse the common bold-prefix declaration without changing the literal signal word, contrast, or hidden-alert rules.
- **FR-008**: Keep tokens out of returned HTML, logs, cookies, session metadata, headers, URLs, and persistent browser storage.
- **FR-009**: Prove actual browser measurements and direct failing geometry, mode, style, and ownership controls.

- **FR-010**: Run affected cases through full `tests/e2e/` collection, including strict mode and unchanged adjacent tests.
- **FR-011**: Use `magenta` and `default` for native acceptance.
  Genuine main-theme asset checks are supplemental only. Add no catalog entries or aliases.
- **FR-012**: Keep the sign-in form and token group within their widths.
  Preserve and separately report the existing dependency-table overflow.

### Key Entities

No database entity, primary key, or persistent credential format changes.
The browser keeps only existing form values, selected mode, control eligibility, and required-field baselines.
Evidence contains rectangles, identifiers, counts, status codes, and absence results, not credential values.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: All four native geometry cells meet the alignment, gap, containment, accessible-name, and label-focus limits.
- **SC-002**: Inactive token controls have zero keyboard reach and zero native FormData entries.
- **SC-003**: Ten cycles create zero requests and zero additional listeners. One subsequent submit creates exactly one request.

- **SC-004**: Both empty client cases create zero requests. The submitted token is empty before a refusal response.
- **SC-005**: All measured native danger prefixes have weight 700 and retain their original colors and signal text.
- **SC-006**: Required guards reject direct bad inputs. Existing process-owner and trail guards remain active.

## Assumptions

The user authorizes only presentation changes. No live Mist call, real credential, production action, or shared harness edit is necessary.
The user authorizes a local validated commit at parent position 38.
No push, PR, merge, Actions run, or delivery completion precedes the explicit parent verified-main SHA grant.

The mandatory SpecKit hook failed because PowerShell is absent.
The specification, plan, and tasks use the authorized feature-only template equivalent.
No shared `.specify` state or governance file changes.
