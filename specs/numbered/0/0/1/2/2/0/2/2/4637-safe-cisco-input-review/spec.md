# Feature Specification: Safe Cisco Input and Structured Review

**Feature Branch**: `feat/4637-cisco-input-review`

**Created**: 2026-11-26

**Status**: Draft. Offline review only. Cloud calls stay blocked.

**Input**: GitHub issue 4637, "[Spec]: Add safe Cisco input and structured review". The issue completes tasks T007 to T010 of the full-parity task map in `specs/live/0/0/0/1/2/1/3/3/2/1/4/2/1/4/1/3/0/20261105-170040-cisco-converter-full-parity/tasks.md`. Parent issue 4224. Prerequisite issue 4636.

## Clarifications

### Session 2026-11-26

- Q: Does this issue register the converter in the shared portal? A: No. Open PR #4208 owns `web_portal/app.py` and `web_portal/templates/base.html`. Source: issue 4637, Migration and Compatibility.
- Q: Does this issue keep uploaded files? A: Only when the operator selects retain and the host enables retention. Production retention stays disabled. Decisions D-7 and D-11.
- Q: Does the catalog show original file names? A: No. The catalog shows an opaque identifier and safe metadata. Decision D-8.
- Q: Which parser families does the review show? A: Eleven families for rows C07 to C17. Conversion stays out of scope. Decision D-13.
- Q: Which change must land first? A: Issue 4636. It replaces `models.py` and sets the `state/` layout. Source: issue 4637, Implementation Notes.

## Terms

- **Selection**: One input that the operator chooses. A selection is either an upload or a stored input.
- **Upload**: A file that the browser sends in one request. Uploads stay in memory by default.
- **Stored input**: A file that the operator chose to keep in the private input folder.
- **Source**: The validated text of one selection. The source exists only in memory.
- **Observation**: A display-only item that the parser recognizes. An observation converts nothing.
- **Unsupported line**: A source line that the parser does not recognize. It keeps its line number and command category.
- **Review**: The operator approval of one preview. A new preview or a changed selection revokes the review.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Choose a safe input (Priority: P1)

An engineer chooses a stored input or uploads a file. The portal validates the selection before it parses the text.

**Why this priority**: Unsafe input can reach the parser or the private folder. Each later step depends on this check.

**Independent Test**: Use synthetic files and blocked external requests. Each unsafe selection returns a safe error and creates no file.

**Acceptance Scenarios**:

1. **Given** a stored input in the private folder, **When** the engineer selects its identifier, **Then** the portal previews that input and returns no file path.
2. **Given** a file with a path-like name, **When** the engineer uploads it, **Then** the portal returns 400 and parses nothing.
3. **Given** exactly 16,777,216 bytes of UTF-8 text, **When** the engineer uploads it, **Then** the portal accepts the file.
4. **Given** one byte more than the limit, **When** the engineer uploads it, **Then** the portal refuses the file before decoding.

### User Story 2 - Read structured observations (Priority: P1)

An engineer reads one display-only section for each observed family. Unsupported lines appear in a separate section.

**Why this priority**: The review shows what the source contains. It must not present a guess as a converted setting.

**Independent Test**: Use one synthetic source for each family. Check each section and the unsupported section with no network call.

**Acceptance Scenarios**:

1. **Given** a source with an interface address, **When** the engineer opens the review, **Then** the interfaces section shows the address and the mask.
2. **Given** a source with a local account, **When** the engineer opens the review, **Then** the identity-access section shows the account without its secret value.
3. **Given** an unknown line, **When** the engineer opens the review, **Then** the unsupported section lists the line number and the command category only.

### User Story 3 - Stop stale approvals (Priority: P1)

A changed selection, name, type, or retention flag revokes the preview and the review.

**Why this priority**: An approval must bind the exact proposal that the engineer reviewed.

**Independent Test**: Preview, review, change one field, and request export.

**Acceptance Scenarios**:

1. **Given** a reviewed proposal, **When** the engineer changes the selection, **Then** export returns 409 until the engineer reviews a new preview.
2. **Given** a reviewed proposal, **When** the engineer opens the observation review, **Then** the review state does not change.

### User Story 4 - Keep the offline DNS workflow (Priority: P2)

An engineer previews, reviews, and exports the DNS proposal as before.

**Why this priority**: Clients and tests from PR #4226 depend on the current response shapes.

**Independent Test**: Run the existing route, unit, and browser tests. Only import lines change.

**Acceptance Scenarios**:

1. **Given** the existing DNS sample, **When** the engineer previews, reviews, and exports, **Then** each response keeps its current shape.

### Edge Cases

- An empty file, a whitespace-only file, or a file with a null character returns 400.
- A file with invalid UTF-8 returns 400.
- A name with a path separator, a drive colon, a UNC prefix, a parent reference, or a control character returns 400.
- A stored identifier with a path, an uppercase letter, or a wrong length returns 400.
- A symbolic link in the private folder stays out of the catalog. Retrieval refuses it.
- A save collision returns 409 and leaves the existing file unchanged.
- A banner body stays out of the observations and appears as unsupported lines.
- A malformed mask has status `malformed`. A repeated directive has status `duplicate`.
- A source with no hostname shows the identity section with status `not-observed`.
- A request with a file and a stored identifier returns 400.
- A retain request with retention disabled returns 400 and creates no file.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The converter MUST list only contained, supported, stored inputs in the catalog.
- **FR-002**: The converter MUST prepopulate the stored selection list from the catalog. It MUST accept a stored selection by identifier only.
- **FR-003**: The converter MUST validate each selection before parsing. One rule set covers suffix, size, encoding, text, and name.
- **FR-004**: The converter MUST accept exactly 16,777,216 bytes. It MUST refuse one more byte before decoding.
- **FR-005**: The converter MUST refuse traversal, drive, UNC, and symbolic-link forms. It MUST NOT accept a client path.
- **FR-006**: Saving MUST create a new file with exclusive creation. A collision MUST return 409 and MUST NOT overwrite a file.
- **FR-007**: Uploads MUST stay in memory by default. Saving MUST require the retain field and an enabled retention object.
- **FR-008**: Stored inputs MUST sit under `data/cisco_config_converter/input/`. No route MUST return a stored file body.
- **FR-009**: The catalog MUST report the identifier, suffix, byte count, and UTC modification time only.
- **FR-010**: A change to the selection, name, type, or retention flag MUST revoke the preview, the review, and the export.
- **FR-011**: The observation review MUST show eleven display-only families. It MUST NOT convert a setting or call Mist.
- **FR-012**: The review MUST list each unsupported line in a separate section with its line number and command category.
- **FR-013**: The review MUST show object names and network values. It MUST omit descriptions, identity values, credentials, communities, keys, and banner text.
- **FR-014**: The review MUST give each malformed mask, duplicate directive, and ambiguous interface an explicit status.
- **FR-015**: The preview, review, and export responses MUST keep their current shapes. The observation route MUST NOT change the review state.
- **FR-016**: The existing DNS preview, review, and export behavior MUST stay unchanged.
- **FR-017**: Logs MUST omit source text, file names, and secret values. Each action MUST log before and after the action.
- **FR-018**: This change MUST NOT change `web_portal/app.py` or `web_portal/templates/base.html`. It MUST NOT register a shared route.
- **FR-019**: Each new interactive control MUST carry a stable `data-testid` attribute and MUST support keyboard use.
- **FR-020**: Unsafe input MUST return a safe 400 or 409 response. The response MUST NOT show a path or a traceback.
- **FR-021**: Each touched executable line MUST carry an inline comment. Each directory in the change MUST hold five children or fewer.
- **FR-022**: Tests MUST use synthetic fixtures, `tmp_path`, blocked sockets, and no Mist call.

### Mist Cloud Transport Requirements

This feature names no mistapi method. It makes no Mist REST request. It opens no WebSocket transport. The pinned mistapi package stays unchanged in `requirements.txt`.

### Key Entities

- **SourceSelection**: One validated source with its origin, suffix, byte count, and SHA-256 digest. It exists only in memory.
- **StoredInput**: One private file with an opaque identifier, a suffix, a byte count, and a creation time.
- **ObservationSection**: One family with a fixed title, a status, and its observation items.
- **ObservationItem**: One recognized line with its line number, label, value or omitted marker, and status.
- **UnsupportedLine**: One unrecognized line with its line number and command category.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The exact 16,777,216-byte test passes. The one-byte test refuses the file before decoding.
- **SC-002**: All 40 planned test functions pass, and the run reports zero skipped tests.
- **SC-003**: The test run records zero socket attempts and zero Mist calls.
- **SC-004**: Each of the eleven families has one positive test and one negative test.
- **SC-005**: The existing route, unit, and browser tests pass with import changes only.
- **SC-006**: The browser journey tests pass with `UPGRADE_PORTAL_E2E_STRICT` set to `1`.
- **SC-007**: The coverage report for `src` stays at 80 percent or above.
- **SC-008**: Each new function has cyclomatic complexity 10 or less. Pylint reports 9.5 or above for `src/`.

## Assumptions

- Issue 4636 lands before implementation starts. This record follows its `state/` layout and its `models.py` move.
- The private input folder stays empty in production until the owner approves enablement and the exclusion change lands.
- Windows may refuse symbolic-link creation in a test run. The tests use a documented fallback and never skip.
- The container user with UID 1000 writes under `data/` only after retention is enabled.
- The orchestrator authorizes the merge before the merge task runs.

Caution: A changed selection clears the review. The engineer must preview again before export.

## Out of Scope

- Conversion of any family into a Mist setting. Issues 4638 to 4640 own those changes.
- Mist discovery, apply, administration, restore, and recovery. Issues 4642 to 4646 own those changes.
- Shared portal registration and navigation. Issues 4633 and 4648 and PR #4208 own those changes.
- Production enablement of stored inputs. An owner approval and an exclusion change come first.
- Changes to the shared data browser and the output scan.
- DHCP overlap analysis and role or hardware selection. Issues 4640 and 4638 own those changes.
- Visual parity journeys. Issue 4647 owns those changes.
- Licensing and source reuse. Issue 4635 owns that decision.

Warning: Enabling stored inputs before the exclusion change exposes customer configuration through the shared data browser. Keep retention disabled until decision D-11 closes.
