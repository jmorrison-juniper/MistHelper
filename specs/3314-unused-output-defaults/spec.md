# Feature Specification: Remove Unused Output Defaults

**Feature Branch**: `jmorrison-juniper-unused-output-defaults` is app-managed.

**Created**: 2026-10-01

**Status**: The local repair is verified. Authorized publication is in progress.

**Input**: Repair existing issue #3314 with option 2. Remove three unused settings and correct the SQLite selection instruction.

**Issue**: [Issue #3314](https://github.com/jmorrison-juniper/MistHelper/issues/3314)

**Claim**: [The existing claim](https://github.com/jmorrison-juniper/MistHelper/issues/3314#issuecomment-5936991593) belongs to `jmorrison-juniper`.

**Session**: `694ad69e-4090-4f3e-91bd-4bc197e768be`

**Initial Base**: `ff3cc1bea8ab58026210a968ff1465f61c9fec78` is a local reference, not publication permission.

**Feature Directory**: `specs/3314-unused-output-defaults`

**Current Artifact**: This phase writes only `specs/3314-unused-output-defaults/spec.md`.

The session script and both image files declare a SQLite default that MistHelper does not use.
MistHelper selects CSV unless the operator supplies the SQLite flag.
This repair removes the false default.
It does not change export selection, readiness policy, or stored data.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Keep the Existing CSV Default (Priority: P1)

As an SSH operator, I need configuration that describes the actual default.
My existing CSV export workflow must not change.

**Why this priority**: An automatic change to SQLite can leave an operator without the expected CSV file.
Option 2 avoids that change.

**Independent Test**: Check all three configuration sources before and after the repair.
Execute the actual session script with a synthetic application.
Verify the existing default selection and local CSV export.

**Acceptance Scenarios**:

1. **Given** the original configuration, **When** the contract checks all three sources, **Then** it fails and names all three unused settings.
2. **Given** the repaired configuration, **When** the same contract checks those sources, **Then** all three checks pass.
3. **Given** no format flag, **When** the operator requests an export, **Then** CSV remains the selected local format.
4. **Given** an isolated session, **When** the script starts the synthetic application, **Then** it adds neither an output setting nor a format flag.

### User Story 2 - Select SQLite Explicitly (Priority: P1)

As an operator, I need one correct instruction for SQLite selection.
I must supply `--output-format sqlite` to select the existing local SQLite export.

**Why this priority**: The current instruction offers an environment setting that does not select the export format.

**Independent Test**: Check the corrected instruction and the existing format parser.
Verify local exports with two synthetic records.

**Acceptance Scenarios**:

1. **Given** the corrected data-model page, **When** the operator reads its SQLite instruction, **Then** that instruction requires `--output-format sqlite`.
2. **Given** an explicit SQLite flag, **When** the parser and exporter process synthetic records, **Then** they retain the existing SQLite treatment.
3. **Given** an explicit CSV flag, **When** the environment names SQLite, **Then** the selected local export remains CSV.
4. **Given** `--output-format polyglot`, **When** the parser processes the request, **Then** it rejects that unsupported flag value.

### User Story 3 - Preserve Readiness and Session Controls (Priority: P1)

As an operator, I need the same readiness results and session controls.
The repair must not change credential handling or restart behavior.

**Why this priority**: Readiness and session controls have real readers.
Removing their configuration would exceed this repair.

**Independent Test**: Execute the actual Bash script with isolated paths and synthetic credentials.
Exercise readiness decisions with replacements for all resource checks.

**Acceptance Scenarios**:

1. **Given** the compose configuration, **When** readiness reads `OUTPUT_FORMAT=polyglot`, **Then** it retains the ArangoDB and Redis checks.
2. **Given** no readiness format setting, **When** readiness selects its checks, **Then** its existing SQLite default remains unchanged.
3. **Given** either supported token name, **When** an isolated session starts, **Then** credential transfer works without exposing the token.
4. **Given** no supported token, **When** a session starts, **Then** it exits with status 1 before any application launch.
5. **Given** isolated sessions and controlled application exits, **When** the script runs, **Then** isolation, cleanup, and restart results match the original script.

### User Story 4 - Verify the Repair Without Publication (Priority: P2)

As a maintainer, I need evidence that the contract detects the original defect.
I also need evidence that it rejects new false defaults.
All delivery work must remain within the assigned files and publication boundary.

**Why this priority**: A contract that passes without checking its inputs does not protect operators.
Separate artifacts also prevent changes to shared feature state.

**Independent Test**: Run the contract against original, repaired, and invalid temporary inputs.
Inspect its checked counts and the final changed-file list.

**Acceptance Scenarios**:

1. **Given** a restored unused setting, **When** the contract checks a temporary input, **Then** it rejects that input.
2. **Given** incorrect SQLite instructions, **When** the contract checks the temporary page, **Then** it rejects that page.
3. **Given** an unreadable required input, **When** the contract runs, **Then** it fails and reports accurate checked counts.
4. **Given** completed local work, **When** publication permission is absent, **Then** the session stops before a push or pull request.

### Edge Cases

- An inherited `OUTPUT_FORMAT` value does not select the CLI export format.
  Removing declarations must not add an `unset` operation.
- A setting with another value is still unused in the three repair sources.
  Comments alone are not active settings.
- A page without the required SQLite flag is not a valid documentation repair.
  A page that offers environment-only selection is also invalid.
- Missing contract inputs must cause failure.
  Missing session credentials must retain the script's existing refusal behavior.
- Missing tools, missing dictionary support, and empty coverage reports must not appear as successful validation.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Remove only `export OUTPUT_FORMAT=sqlite` from `container/scripts/misthelper-session.sh`.
  Remove only `ENV OUTPUT_FORMAT=sqlite` from `Dockerfile` and `Containerfile`.
- **FR-002**: Correct only the SQLite selection instruction in `documentation/wiki/Data-Model.md`.
  Require `--output-format sqlite`.
  Do not claim that `OUTPUT_FORMAT=sqlite` selects CLI exports.
- **FR-003**: Preserve the parser's CSV default and its `csv` and `sqlite` choices.
  Do not add environment-based defaults, new flag values, or format logging.
- **FR-004**: Preserve existing CSV and explicit SQLite parse and export treatment.
  Preserve record values, existing key treatment, and local output selection.
- **FR-005**: Keep `compose.yml` byte-identical to the initial base.
  Retain `OUTPUT_FORMAT=polyglot`.
- **FR-006**: Keep `web_portal/routes/dashboard.py` byte-identical to the initial base.
  Retain its environment reader, normalization, SQLite default, check selection, and readiness responses.
- **FR-007**: Apart from the single removed export, keep the session script byte-identical to the initial base.
  Preserve credential transfer, session identifiers, cleanup, restart controls, and application arguments.
- **FR-008**: Validate actual Bash parsing and actual session execution.
  Use isolated `tmp_path` storage and a synthetic application instead of the production application.
- **FR-009**: The contract must check every required input and report expected, checked, and rejected counts.
  It must fail on unreadable input and reject unused settings and incorrect documentation.
- **FR-010**: Use synthetic values only.
  Tests must use no network, real credentials, production ports, or production stores.
- **FR-011**: Keep `Dockerfile` and `Containerfile` byte-identical after the repair.
  Build locally through owned Podman when that capability is available.
- **FR-012**: Run the applicable configured local gates during later validation.
  Do not change dependencies, pins, quality baselines, suppressions, exclusions, or gate thresholds.
- **FR-013**: Give each requested phase its own artifact in the named feature directory.
  This phase must write only `spec.md`.
  Do not create shared feature state or requirement checklists.
- **FR-014**: Use Simplified Technical English with short, complete sentences.
  Keep comments rare.
  Explain the reason for a non-obvious decision.
- **FR-015**: Keep delivery local until the parent explicitly grants publication against a verified current base.
  Initial references and sibling reports do not grant permission.

### Scope and File Ownership

This is an existing claimed repair.
It is not a new numbered feature or a new branch.
The product change contains three configuration deletions and one documentation correction.

The four principal paths are:

- `container/scripts/misthelper-session.sh`
- `Dockerfile`
- `Containerfile`
- `documentation/wiki/Data-Model.md`

The requested phase records have separate paths:

| Phase | Owned artifact |
| --- | --- |
| Specify | `specs/3314-unused-output-defaults/spec.md` |
| Plan | `specs/3314-unused-output-defaults/plan.md` |
| Tasks | `specs/3314-unused-output-defaults/tasks.md` |
| Implement | `specs/3314-unused-output-defaults/validation.md` records execution evidence. |
| Analyze | `specs/3314-unused-output-defaults/analysis.md` |

The reserved test package contains exactly these five paths:

- `tests/unit/container/output_defaults/__init__.py`
- `tests/unit/container/output_defaults/contract.py`
- `tests/unit/container/output_defaults/session.py`
- `tests/unit/container/output_defaults/test_contract.py`
- `tests/unit/container/output_defaults/test_session.py`

The reserved release note is `changelog.d/issue-3314-unused-output-defaults.md`.
The full reservation contains 15 files.
Only this specification is writable during the current phase.
Later reservations do not authorize changes now.

Do not edit `MistHelper.py`, the CLI parser, or any file under `src/`.
Do not edit `container/scripts/write-session-env.sh` or deployment environment examples.
Do not edit `README.md`, `CHANGELOG.md`, instructions, shared agent context, or other specifications.
Do not edit `.specify/feature.json`, `.spec-context.json`, or branch metadata.
Do not change SDK pins, database schemas, primary keys, quality baselines, suppressions, or exclusions.
Do not create requirement checklists.
Do not invoke Git hooks or Git extensions.
Do not stage or commit files during this phase.
Do not create or change issues or pull requests.

Issue #3313 owns the database-password allowlist repair.
That repair is outside this scope.
Do not perform production authentication, firmware operations, or production datastore operations.
Do not perform migration.

### Validation Requirements

#### Contract Evidence

Create the contract before changing the three configuration files or the documentation page.
Record its failure against the initial base.
Run that unchanged contract after the repair.
Do not weaken the contract to produce a successful result.

The contract reads six required inputs:

| Input group | Required count | Required decision |
| --- | --- | --- |
| Session script and image files | 3 | Each source contains no active `OUTPUT_FORMAT` assignment. |
| Data-model page | 1 | Its SQLite instruction requires the flag and offers no environment-only alternative. |
| Compose and readiness files | 2 | Both files retain the required existing settings and decisions. |

The original inputs must produce three configuration failures and one documentation failure.
The report must state that it checked all six inputs.
The repaired inputs must produce zero failures with six checked inputs.

Use repaired temporary copies for these 14 negative cases:

- Restore the original unused setting in each configuration source separately.
  These are three cases.
- Inject an active `OUTPUT_FORMAT=polyglot` setting into each configuration source separately.
  These are three additional cases.
- Restore the false environment-selection instruction, then test an instruction without the required flag.
  These are two separate documentation cases.
- Make each of the six required inputs unreadable separately.
  These are six additional cases.

Every negative case must fail.
Each unreadable-input case must name its path and report six expected inputs and five checked inputs.
Only successfully read inputs count as checked.
Do not replace unreadable input with empty content or a passing result.

#### Format Selection and Export Evidence

Exercise the existing parser and exporter, not duplicate selection logic.
Use these 15 valid cases:

| Environment `OUTPUT_FORMAT` | No format flag | Explicit `--output-format csv` | Explicit `--output-format sqlite` |
| --- | --- | --- | --- |
| Unset | CSV | CSV | SQLite |
| `csv` | CSV | CSV | SQLite |
| `sqlite` | CSV | CSV | SQLite |
| `polyglot` | CSV | CSV | SQLite |
| `synthetic-unsupported` | CSV | CSV | SQLite |

Each case uses two synthetic records.
Verify the parsed selection and the actual selected local export.
Verify both records in the result.
In isolated local mode, a CSV case must not create a SQLite result.
A SQLite case must not create a CSV result.
Keep optional remote writes inactive through isolated test controls.
Do not change production export code.

Also verify that `--output-format polyglot` fails even when the environment contains `polyglot`.
That value remains a readiness setting, not a supported CLI choice.

#### Session and Readiness Evidence

Run `bash -n` against the actual session script.
Also prove that a malformed temporary copy fails Bash parsing.
Execute the actual script with every operational test path under `tmp_path`.
Replace only the launched application with a synthetic recorder.
Do not start SSH or execute the production application.

The session evidence must cover these outcomes:

- A clean application exit returns status 0 after exactly one launch.
  The launch retains the original arguments and adds no format flag.
- Both `MIST_APITOKEN` and `MIST_API_TOKEN` remain supported.
  Test credential transfer from an isolated session file and from the supplied test environment.
  Missing credentials return status 1 with zero application launches.
- Two distinct synthetic `SSH_CONNECTION` values retain separate session identifiers.
  Each session removes only its own marker.
  Existing signal cleanup remains unchanged.
- Consecutive failed starts stop at the configured attempt limit.
  Delay doubling, the delay cap, and the healthy-run reset remain unchanged.
  Preserve defaults of five attempts, 30 healthy seconds, two initial seconds, and a 60-second cap.
- Each session test has a 30-second timeout.
  Use existing overrides to avoid extended waits.
  Captured output and logs must contain no synthetic token values.

Readiness evidence must retain both general resource checks.
Unset format, `sqlite`, and `standalone` retain the SQLite check.
Normalized `polyglot` retains ArangoDB and Redis checks without a SQLite check.
CSV and unsupported values retain the existing general-only behavior.
Healthy checks retain status 200.
Any failed check retains status 503 and its failure name.
Replace all resource checks so these tests make no network calls or production writes.

#### Local Quality Gates

These gates are requirements for later validation, not claims of execution during this phase.
Record commands, scope, checked counts, results, and missing capabilities in `validation.md`.

| Gate | Required local evidence |
| --- | --- |
| Ruff | Run `python -m ruff check .` with the full configured scope. |
| Black | Run `python -m black --check --diff .` with the full configured scope. |
| mypy | Read `MYPY_PATHS` from `.github/workflows/ci.yml`. Run exactly that scope with `--config-file pyproject.toml` when applicable. State any non-applicability reason. |
| Bandit | Run `python -m bandit -c pyproject.toml -r .`. Retain all configured severity checks and exclusions. |
| Test-quality ratchet | Use the unchanged `.github/test-quality-config.toml` and `.github/test-quality-baseline.json`. Retain the CI scope rules and full-scope triggers. Record `gate_scope` and checked test counts. |
| Markdown links | Validate local targets and anchors in feature-owned Markdown without network access. State which external links remain unverified. |
| STE | Apply `documentation/ASD-STE100_writing-guide.md` and `.ste-linter.toml`. Retain the configured score floor of 80. Report linter and dictionary availability. |
| Focused tests and coverage | Run the reserved test package. Record executed cases, skips, covered files, missing lines, and the coverage denominator. Meet existing configured floors. |

Required tests must have zero skips and zero unresolved failures.
Every critical contract decision must have valid and invalid test evidence.
A coverage report with zero measured lines is not a pass.
If repository settings omit test helpers, measure them separately without changing repository exclusions or thresholds.
Do not add dependencies or update SDK or tool pins.
Do not change baselines or add suppressions to obtain successful gate results.

#### Image Evidence and Capability Limits

Compare the complete bytes of `Dockerfile` and `Containerfile`.
Both files must remain identical after their single-line deletions.
All other bytes in each image file must match the initial base.

Before a build, verify that Podman targets an owned local runtime.
If available, build from both image files with issue-specific local image names.
Do not replace a production image tag.
Do not push images, start containers, deploy services, or use production ports or stores.
Do not start a bare Podman container.

If Podman, PowerShell, or dictionary support is missing, report the missing capability.
Do not report the affected build or gate as passed.
The specification phase does not require an image build.

### Local-Only Delivery Boundary

Publication position is 18, after issue #3300.
Parent PR #3687 has its own publication window.
Do not publish during that window.

Stop before any push or pull request.
Proceed only after the parent explicitly grants publication against a verified current base.
An observed `main` revision is not permission.
The initial SHA is not permission.
Sibling reports are not permission.
Do not commit shared feature state in any later phase.

The parent granted sole position-18 publication and delivery on 2026-10-02.
The granted main is `7a4435bdf8ceff7e1dd527e4d2fd854e79542f37`.
This explicit grant opens the publication boundary after the required current-base proof.
Stop if main advances for an unrelated change or a reserved path has another owner.
Use a protected full-head-match squash merge without an administrative bypass or auto-merge.
Verify the actual resulting main locally and record the delivery receipt.
The parent alone releases the next issue.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: All three configuration sources stop declaring the unused default.
  The two image specifications remain byte-identical.
- **SC-002**: All 15 valid selection cases preserve their expected output and both synthetic records.
  The unsupported explicit selection fails.
- **SC-003**: The unchanged contract fails before the repair and succeeds afterward with six checked inputs.
  All 14 negative cases fail with accurate counts.
- **SC-004**: The SQLite instruction requires explicit selection.
  There are zero instructions that offer environment-only selection on the corrected page.
- **SC-005**: Every listed session and readiness case matches the original behavior.
  Tests make zero network calls and use zero production resources.
- **SC-006**: Every applicable local gate has a recorded result.
  Coverage has a nonzero denominator and meets existing floors.
  Missing capabilities never appear as successful results.
- **SC-007**: This phase creates exactly one file.
  Later records remain unique, and publication stops until the parent grants a verified current base.

## Assumptions

- The selected repair is option 2 from issue #3314.
  Option 1 and an automatic SQLite default are excluded.
- Existing CLI selection and export behavior define the compatibility contract.
  This repair introduces no data entities, schema changes, or migrations.
- The initial checkout matches the supplied branch and SHA.
  The two image files are byte-identical before the repair.
- The user checked complete file lists for all 12 open pull requests and reported no reservation overlap.
  That check does not grant publication permission.
- The active repository specification template resolves to `.specify/templates/spec-template.md`.
  The named artifact workflow does not require shared feature discovery state.
- The initial capability check found the Podman executable.
  Runtime ownership and build capability remain unverified.
  It found no PowerShell executable or `ste-linter` on `PATH`.
  The configured `data/ste_dictionary.json` file is absent.
  This phase did not run implementation gates or image builds.
