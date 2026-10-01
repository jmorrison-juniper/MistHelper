# Feature Specification: Complete Release Note Bodies

**Feature Branch**: `jmorrison-juniper-complete-release-note-bodies`

**Created**: 2026-09-30

**Status**: Implementation prepared for final validation

**Input**: User description: "Create the required SpecKit specification for MistHelper issue #3431. Preserve complete release bodies and both release references."

**Issue**: [MistHelper issue #3431](https://github.com/jmorrison-juniper/MistHelper/issues/3431)

**Feature Directory**: `specs/3431-complete-release-note-bodies/`

**Claimed App Session**: `514c1e99-d8a8-4af5-a5ac-ecad749e0ecd`

**Claimed CLI Session**: `c14839b3-65be-4170-99b7-6f8d04ac3da9`

The release action cuts generated notes to 124,999 characters.
The issue records 216,403 characters and 1,436 pull request lines.
The supplied reproduction records 216,840 characters and 1,439 pull requests.
Its published body ended with `* secur`.
The reproduction lost about 42% of the text and the Full Changelog compare link.

This specification requires a complete release body, not a partial list of changes.
A large release can use a labeled summary instead of the generated notes.
Both output modes must retain the validated compare link and a pinned CHANGELOG reference.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Read a complete large release (Priority: P1)

As a release reader, I need complete text after a long release gap.
I need links to the complete comparison and the CHANGELOG for that release.
The release must explain when a summary replaces the generated notes.

**Why this priority**: The current cut hides recent changes and removes the comparison.
Readers cannot determine which information the release omits.

**Independent Test**: Prepare a source with 216,840 characters, 1,439 pull requests, and a final compare link.
Check the resulting body without a network connection.
The body must contain a complete summary and both required links.

**Acceptance Scenarios**:

1. **Given** a valid source above a size limit, **When** preparation succeeds, **Then** the body contains a labeled summary with both required links.
2. **Given** the long-gap reproduction, **When** preparation succeeds, **Then** no line ends with an accidental cut or a partial pull request entry.
3. **Given** a source with a final compare link, **When** the summary replaces the source, **Then** the summary retains that exact validated destination.
4. **Given** a summary, **When** a reader opens the CHANGELOG reference, **Then** the destination names the current release tag.
5. **Given** a summary, **When** a reader reads its explanation, **Then** the text states that size limits prevent inclusion of the generated notes.

---

### User Story 2 - Read all fitting generated notes (Priority: P1)

As a release reader, I need every generated change when the complete body fits.
The release must not remove text merely because a summary is easier to publish.

**Why this priority**: Small releases must retain their complete generated notes.
The repair must not reduce useful information for ordinary releases.

**Independent Test**: Prepare complete candidates below, at, and above the publication limits.
Include the CHANGELOG reference and the final line ending in each measurement.
Compare the fitting output with the complete source.

**Acceptance Scenarios**:

1. **Given** a complete candidate below both limits, **When** preparation succeeds, **Then** the body preserves all generated text in its original order.
2. **Given** a candidate exactly at the publisher-safe limit, **When** it satisfies the other limit, **Then** preparation retains the complete generated notes.
3. **Given** a source that fits before the CHANGELOG reference, **When** the final candidate exceeds a limit, **Then** preparation selects the summary.
4. **Given** Unicode text, **When** its character count fits but its publisher count exceeds the limit, **Then** preparation selects the summary.
5. **Given** a fitting source without a terminal newline, **When** preparation adds the reference, **Then** it preserves the source and separates complete lines.

---

### User Story 3 - Stop unsafe publication (Priority: P1)

As a release maintainer, I need preparation to stop when required information is invalid.
I need an explicit error and checked counts instead of an empty or misleading release body.

**Why this priority**: Incorrect references can direct readers to unrelated changes.
An unreadable input must not produce a successful release check.

**Independent Test**: Supply invalid inputs and force an output failure.
Each case must fail without a usable publication result.
Check the error phase, checked counts, and absence of sensitive log content.

**Acceptance Scenarios**:

1. **Given** empty, malformed, or unreadable required input, **When** preparation runs, **Then** it fails with an explicit error and checked counts.
2. **Given** a missing compare link, **When** preparation validates the source, **Then** it fails instead of inventing a comparison.
3. **Given** a compare link for another repository or current tag, **When** preparation validates it, **Then** it fails before publication.
4. **Given** an invalid reference or conflicting metadata, **When** preparation validates the context, **Then** it rejects the source.
5. **Given** an unwritable output, **When** preparation writes the body, **Then** it fails and prevents publication.
6. **Given** a summary above a size limit, **When** preparation measures it, **Then** it fails without slicing any text.
7. **Given** a preparation failure and an existing output file, **When** the publish job reaches the failure, **Then** it cannot publish that stale file.
8. **Given** any preparation result, **When** a maintainer reads the logs, **Then** the logs contain phases and counts without tokens or note contents.

---

### User Story 4 - Prove the workflow body source (Priority: P2)

As a reviewer, I need an offline contract check that reads the actual release workflow.
The check must prove that the publisher consumes only the measured body.
The change must preserve existing release triggers, build jobs, and required checks.

**Why this priority**: Correct helper behavior alone cannot prevent the workflow from requesting generated notes again.
A contract check must protect the publication path.

**Independent Test**: Read the workflow and check its publication path.
Test altered workflow samples that bypass preparation or change the body source.
Each invalid sample must fail with checked counts.

**Acceptance Scenarios**:

1. **Given** the valid workflow, **When** the contract check runs, **Then** it proves that preparation precedes publication and supplies the measured file.
2. **Given** the publisher, **When** the check reads its settings, **Then** it requires `generate_release_notes: false` and the measured file through `body_path`.
3. **Given** a publisher with automatic generation or another body source, **When** the check runs, **Then** it fails.
4. **Given** an unreadable or malformed workflow, **When** the check runs, **Then** it fails with an explicit reason and checked counts.
5. **Given** the changed workflow, **When** the check compares release behavior, **Then** the existing tag trigger and build dependencies remain unchanged.
6. **Given** a preparation step that ignores failure, **When** the check runs, **Then** it rejects the publication path.
7. **Given** the helper changes, **When** local validation runs, **Then** all required gates pass without shared configuration changes.
8. **Given** the release-notes document and issue fragment, **When** a reviewer checks them, **Then** both explain the complete-body repair.

### Edge Cases

- An added reference can make a fitting source too large.
  Select the output mode from the complete final candidate.
- A candidate at 124,999 UTF-16 units can pass.
  A candidate at 125,000 UTF-16 units must use the summary.
- The GitHub character limit does not override the stricter publisher-safe limit.
  Apply both limits to the same complete text.
- Characters outside the Basic Multilingual Plane use two UTF-16 units.
  Preserve valid Unicode in the body but keep logs ASCII-only.
- Reject invalid Unicode, including isolated surrogate values that cannot form valid output text.
- Reject a whitespace-only body, an unexpected body type, invalid JSON, or invalid text encoding.
- Reject absent, conflicting, malformed, or incomplete required compare destinations.
- Reject another host, repository, or current tag in the required compare destination.
  Reject credentials, query strings, and fragments in that destination.
- Reject invalid refs and traversal components after reference decoding.
  Do not accept a moving branch as the current release tag.
- Date-based tags can have more than three version fields.
  Do not impose a three-field version rule.
- If the source lacks a compare link for an initial release, fail explicitly.
  Do not guess a previous release.
- If the summary cannot fit, fail explicitly.
  Do not shorten a required reference or remove a complete line.
- If an output write fails or writes incomplete text, fail explicitly.
  Do not report a usable body or continue publication.
- If a required guard cannot read its input, report zero examined inputs and fail.
  Do not treat an unavailable input as a successful skip.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Preparation MUST request generated notes through GitHub's read-only `POST /repos/{owner}/{repo}/releases/generate-notes` endpoint.
  It MUST save the response in a local JSON input file.
  This request MUST NOT create or update a release, draft, tag, or artifact.
- **FR-002**: Preparation MUST require a readable JSON object with a nonempty text body.
  It MUST reject missing input, malformed JSON, invalid encoding, invalid Unicode, and unexpected required field types.
  Whitespace-only text MUST fail.
- **FR-003**: Preparation MUST validate the expected repository, tag event, current tag, and supplied source metadata before body construction.
  Metadata MUST agree with the release context.
  Human-readable release titles MUST NOT substitute for repository or tag identifiers.
  References MUST satisfy Git ref naming rules.
  Encoded reference components MUST decode to the exact validated refs.
- **FR-004**: Preparation MUST require one unambiguous Full Changelog compare destination from the generated source.
  It MUST validate the GitHub host, expected repository, valid base ref, and exact current release tag.
  If the request supplies a previous tag, the base ref MUST match it.
  Missing, wrong, conflicting, or unsafe destinations MUST fail.
- **FR-005**: Every successful body MUST contain a CHANGELOG reference pinned to the current release tag.
  The reference MUST name `CHANGELOG.md` in the expected repository.
  The reference MUST NOT target a moving branch.
  Reference encoding MUST preserve the validated tag.
- **FR-006**: The full candidate MUST contain all generated text and the pinned CHANGELOG reference.
  Preparation MUST preserve the generated text, its order, and its complete lines.
  It MUST add a separator when needed and a terminal newline.
  It MUST NOT slice notes, remove entries, or copy a partial line.
- **FR-007**: Preparation MUST measure the complete candidate under both size limits.
  The GitHub limit is 125,000 Unicode characters.
  The conservative publisher-safe limit is 124,999 UTF-16 units.
  The publisher-safe limit is inclusive.
  Every accepted body contains fewer than 125,000 code points.
  The character count measures Unicode code points.
  The publisher count matches JavaScript string length.
  Measurements MUST include labels, separators, references, and every line ending.
  Byte length MUST NOT replace either count.
- **FR-008**: If the full candidate satisfies both limits, preparation MUST use the complete generated notes.
  If either count exceeds its limit, preparation MUST use a concise summary.
  Preparation MUST NOT shorten the full candidate to make it fit.
- **FR-009**: The summary MUST contain the current release tag, a clear summary label, and a size-limit explanation.
  It MUST contain the same validated compare destination and the pinned CHANGELOG reference.
  It MUST use complete lines and a terminal newline.
  It MUST NOT contain an extracted partial list or invented claims about changes.
- **FR-010**: Preparation MUST measure the complete selected body, including a summary, before it accepts the output.
  If the selected body exceeds either limit, preparation MUST fail.
  It MUST NOT remove required text or shorten references to recover.
- **FR-011**: Preparation MUST write valid UTF-8 text to the publication file.
  It MUST confirm that the measured text matches the file the publisher receives.
  Missing, unreadable, unwritable, or incomplete output MUST fail.
  A failed attempt MUST NOT authorize use of an existing output file.
- **FR-012**: The publisher MUST consume the measured file through `body_path`.
  It MUST set `generate_release_notes: false`.
  It MUST NOT supply a competing inline body or append generated notes.
  Body preparation MUST precede publication within the publish job.
  A required preparation failure MUST prevent the publisher from running.
- **FR-013**: Required preparation and contract guards MUST return failure for invalid or unreadable inputs.
  Errors MUST identify the failed phase and the relevant checked counts.
  Counts MUST state what the guard actually examined.
  An unreadable input counts as zero examined inputs.
  A readable but malformed input counts as one examined input.
  The validation phase reports zero valid records until validation succeeds.
  Required checks MUST NOT report success after a skip.
- **FR-014**: Preparation MUST log phases before each action and result counts after each action.
  Results MUST include the output mode and available source, candidate, and final counts under both counting rules.
  Results MUST include examined input and complete compare-line counts.
  Logs and errors MUST use ASCII text.
  They MUST NOT contain tokens, note contents, or raw response bodies.
- **FR-015**: The helper MUST use semantically named classes and the standard library only.
  It MUST add no dependency and MUST support the project's Python 3.13+ requirement.
  Class ownership, structural limits, comments, and action logging MUST obey the existing constitution.
  Standalone delegation wrappers MUST NOT provide the helper behavior.
- **FR-016**: Offline unit tests MUST cover the required cases in the test matrix below.
  They MUST assert output text, both counts, selected mode, and failure decisions where applicable.
  Required cases MUST NOT need credentials, a live release, or a network connection.
- **FR-017**: An offline contract test MUST read `.github/workflows/release.yml` and prove the real body source.
  It MUST connect the preparation output to the publisher input.
  A matching comment, unused step, or unrelated path MUST NOT satisfy the check.
  Negative cases MUST prove failure for automatic generation, another source, bypassed preparation, and unreadable input.
- **FR-018**: The change MUST preserve existing event filters, concurrency behavior, expensive-job guards, permissions outside preparation, and required statuses.
  It MUST preserve the Python, standalone, version, and container build jobs.
  The publish job MUST retain `needs: [build-python, build-standalone, build-container]`.
  Only publish-body preparation and consumption may change release behavior.
- **FR-019**: The new release-notes document MUST explain both output modes, limits, required links, failures, counts, and local validation.
  The issue fragment MUST explain the complete-body repair.
  The change MUST NOT edit the shared CHANGELOG.
- **FR-020**: Future implementation validation MUST use its own Python 3.13+ environment.
  It MUST run targeted pytest with coverage, compile checks, Ruff, Black, mypy, Bandit, and link checks.
  It MUST run the existing repository test-quality ratchet without changes.
  It MUST report actual results and checked scope.
- **FR-021**: Validation MUST NOT change baselines, exclusions, thresholds, dependencies, bootstrap files, or shared instruction files.
  It MUST NOT add suppressions to hide findings.
  Explicit validation MUST include the new helper even when a broad repository gate excludes scripts.

### Required Test Matrix

The tests operate without a network connection.
Size fixtures measure the complete candidate, not only the generated source.

| Case | Required evidence |
|------|-------------------|
| Publisher boundary | Check 124,998, 124,999, and 125,000 UTF-16 units. Select full, full, and summary when the other limit permits. |
| GitHub boundary | Check 124,999, 125,000, and 125,001 characters. Report exact counts and obey the stricter publisher-safe limit. |
| Added text | Show that references, labels, separators, and the terminal newline can change the selected mode. |
| Long gap | Use 216,840 characters and 1,439 pull requests. Retain the complete final compare destination in a labeled summary. |
| Complete source | Compare all fitting generated text with the output. Check the original order and complete final lines. |
| Unicode | Check non-ASCII text, combining characters, and characters outside the Basic Multilingual Plane. Prove that the two counts can differ. |
| Invalid text | Reject invalid encoding, isolated surrogates, whitespace-only text, and unexpected body types. |
| Required input | Reject empty, missing, unreadable, and malformed input. Assert the error and checked counts. |
| Release context | Accept valid date-based tags. Reject invalid refs, traversal, absent metadata, and metadata conflicts. |
| Compare destination | Reject missing links, wrong hosts, wrong repositories, wrong current tags, invalid bases, and conflicting destinations. |
| Pinned reference | Check the current tag and `CHANGELOG.md` destination. Reject a moving-branch destination or invalid reference encoding. |
| Summary limit | Reject a selected summary that still exceeds a limit. Prove that the guard does not slice it. |
| Output failure | Force a write failure, incomplete output, and unusable output paths. Prevent acceptance of stale output. |
| Log safety | Check phases, modes, source counts, final counts, and examined counts. Reject token or note-content exposure. |
| Workflow source | Read the actual workflow. Prove preparation order, `body_path` ownership, and disabled automatic generation. |
| Contract failures | Alter the generation setting, body source, or failure handling. Each case must fail with checked counts. |
| Unreadable guard input | Make the contract input unreadable or malformed. Require failure instead of a successful skip. |
| Preserved behavior | Check the exact tag trigger, existing build jobs, publish dependencies, and unchanged required guard behavior. |

### Key Entities *(include if feature involves data)*

- **Release context**: The expected repository, tag event, current tag, and any explicit previous tag.
  It identifies the release and the required reference destinations.
- **Generated source**: The local response record and its complete note body.
  Its required compare destination must agree with the release context.
- **Release body**: The full body or labeled summary that satisfies both limits.
  It contains the validated compare destination and pinned CHANGELOG reference.
- **Preparation result**: The output mode, examined counts, text counts, and success or failure state.
  Only a successful result authorizes the publisher to consume the measured file.

### Scope and Constraints

The later implementation has this exact file scope:

| Path | Purpose |
|------|---------|
| `.github/workflows/release.yml` | Build and consume the measured release body inside the publish job. |
| `scripts/release_body.py` | Provide the standard-library class helper for validation, body selection, measurement, and output. |
| `tests/unit/test_release_body.py` | Prove body behavior and failure decisions without a network connection. |
| `tests/contract/test_release_body_workflow.py` | Prove the actual workflow source policy and guard failures. |
| `documentation/release-notes.md` | Explain the release-body policy and validation. |
| `changelog.d/issue-3431-complete-release-note-bodies.md` | Record the user-visible repair in one unique fragment. |
| `specs/3431-complete-release-note-bodies/` | Hold the issue-specific SpecKit files. |

This specification command writes only `spec.md` and `checklists/requirements.md` in the reserved feature directory.
It does not create a plan, tasks, implementation files, or additional state files.
It leaves `.specify/feature.json` unchanged.
Downstream commands must use the explicit feature directory.

The app already selected the branch.
Do not create, switch, or rename a branch for this command.
Do not run Git auto-commit hooks, commit, push, create a pull request, or start a workflow.
Do not publish a release, create a tag or draft, or upload artifacts.
Do not modify files in another worktree.

Do not edit `agents.md`, `CLAUDE.md`, `README.md`, requirements, `CHANGELOG.md`, bootstrap files, or shared instruction and configuration files.
Do not change release schedules, packages, images, dependency pipelines, or artifact lists.
Do not add dispatch events, broad branch events, or additional expensive jobs.

The current release trigger is only `push` with `tags: ['v*.*.*']`.
The workflow has no explicit concurrency setting.
Preserve that behavior instead of adding a new concurrency policy.
Preserve the existing version job and pinned container workflow.
Preserve required checks and guards in other workflows without editing those workflows.

The [constitution](../../.specify/memory/constitution.md), version 1.5.0, remains binding.
Future planning must record any conflict between structural limits and the required file locations.
It must resolve that conflict without treating existing debt as permission for new debt.
This specification does not authorize unrelated restructuring or a constitution amendment.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The 216,840-character, 1,439-pull-request case produces a complete labeled summary with zero accidentally cut lines.
- **SC-002**: Every accepted body contains the correct complete comparison and the CHANGELOG reference for the current release tag.
  No accepted reference targets another repository or a moving current branch.
- **SC-003**: Every fitting case preserves 100% of the generated text in its original order.
  No fitting case loses a character or change entry.
- **SC-004**: Every accepted body satisfies both defined publication limits after inclusion of all references and line endings.
  All exact boundary cases produce the specified decision.
- **SC-005**: Every required invalid-input and output-failure case stops publication with an explicit error and accurate checked counts.
  Zero required cases pass through an unavailable-input skip.
- **SC-006**: In both output modes, a reader reaches the complete comparison and pinned CHANGELOG with one link selection for each destination.
  The summary clearly explains why the release omits the generated list.
- **SC-007**: Every tested body-source policy violation fails the offline contract check.
  A reviewer can trace each accepted body to the measured publication file.
- **SC-008**: The repair preserves all existing release triggers, build dependencies, expensive-job guards, and required statuses.
  No unrelated publication behavior changes.

## Assumptions

- The current tag event supplies the expected repository and complete release tag.
  Preparation validates these inputs before it trusts the generated source.
- The generate-notes response supplies a human-readable name and body.
  The response does not need to repeat repository or tag fields.
  Required repository and tag metadata come from the request context.
  If the source also supplies these fields, they must agree.
- GitHub selects the previous comparison base when the request does not name one.
  Preparation accepts that valid base only when the destination ends at the exact current release tag.
- A complete generated response remains the source for fitting releases.
  The fallback is a labeled summary, not a claim that it lists every pull request.
- The CHANGELOG reference targets the file at the current tag.
  A version-section anchor is not required.
  This choice avoids dependence on heading formats.
- The 124,999-unit publisher-safe limit is a deliberate conservative bound.
  A body can satisfy GitHub's character limit and still require the summary.
- Existing credentials authorize note generation during an ordinary release run.
  A request failure stops preparation.
  Offline tests use local fixtures and do not need these credentials.
- The pinned `misthelper-devtools` v0.5.2 has no shared release-body helper.
  This issue does not change that pin or add a dependency.
- Release preparation files are local inputs for the publish job.
  They are not application data exports or additional uploaded artifacts.
- Existing constitution rules govern the later implementation and its local validation.
  This specification-only command does not start the deployment process.
- These ordinary choices are resolved.
  No user clarification is required before planning.
