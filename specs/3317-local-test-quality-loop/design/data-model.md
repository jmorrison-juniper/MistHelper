# Data Model: Local Test-Quality Loop

**Specification**: [spec.md](../spec.md)

**Plan**: [plan.md](../plan.md)

This feature adds no database or persistent application record.
The entities below describe transient guardrail and fixture evidence.
They do not require one Python class per entity.
Group related values when a method would exceed five parameters.

## LocalGuide

| Field | Meaning |
|-------|---------|
| `path` | One of the three required repository-relative document paths |
| `heading_chain` | Exact section heading and required parent heading |
| `shell_profile` | Supported Bash or PowerShell fenced-command syntax |
| `procedure` | Active base preparation, preflight, scoped command, and full-suite command |
| `decision` | Complete validation result with named control errors |

Each guide relates to one live `GateContract`.
A heading inside a comment, quote, or code fence does not locate a section.
The section ends at the next heading with the same or a higher level.
The local-first section must occur under Part 3.

The active procedure uses the labels in [local-commands.md](contracts/local-commands.md).
A valid unused example cannot replace a missing or incorrect active procedure.
Duplicate active labels fail as ambiguous input.

## GateContract

| Field | Meaning |
|-------|---------|
| `source` | Workflow path, job `test_quality_gate`, and step `Run test quality ratchet` |
| `scoped_controls` | Decoded gate, settings, baseline, intended base, and additional trigger controls |
| `full_controls` | Same gate, settings, and baseline without changed-scope controls |
| `explicit_paths` | Distinct additional paths decoded from live CI |
| `automatic_paths` | Settings and baseline paths from the decoded command |

The effective trigger set is the union of both path sets.
Current sizes are two explicit paths, two automatic paths, and four effective paths.
These sizes are observations, not cached expectations in the new guard.

Missing jobs, duplicate named steps, malformed arrays, or unsupported scripts fail contract decoding.
Push and manual execution retain the empty scope array.
The guard never executes workflow text.

## BaseReference

| Field | Meaning |
|-------|---------|
| `variable` | Intended base variable, `BASE_REF` |
| `remote` | Remote-tracking prefix `origin/` |
| `fetch_target` | Matching `refs/remotes/origin/<intended-base>` destination |
| `comparison` | Two endpoints: the resolved intended base and `HEAD` |
| `resolved_revision` | Observed commit in a fixture or operator check |

Documentation checks validate the variable, expansion, fetch destination, and comparison token.
They cannot discover the operator's intended branch from prose.
The operator sets that value and verifies its resolved commit.
Fixture tests supply known local references with explicit expected revisions.

## InputProgress

| Field | Meaning |
|-------|---------|
| `attempted_inputs` | Required paths whose read operations began |
| `read_inputs` | Paths whose UTF-8 reads completed |
| `validated_inputs` | Inputs whose required validation succeeded |
| `read_guides` | Guide paths in `read_inputs` |
| `checked_guides` | Guides with completed pass or failure decisions |

Counts come from these recorded sets.
Reading a malformed file increases `read_inputs`, not `validated_inputs`.
A failed read increases `attempted_inputs` only.
A missing CI contract prevents guide comparisons.
It does not erase successful independent settings or baseline reads.

The required input manifest contains the three guides, CI workflow, settings, and baseline.
Do not treat the old four-file document-plus-CI set as complete.

## GuardrailResult

| Field | Meaning |
|-------|---------|
| `status` | Pass only when all required decisions succeed |
| `inputs` | Measured `InputProgress` |
| `paths` | Successfully decoded explicit, automatic, and effective path sets |
| `errors` | Named input, section, or control errors |

Path counts measure distinct decoded live controls.
They do not multiply by the number of guides.
They do not claim that a trigger file's content was readable.
Input counts provide that separate evidence.

Every result includes counts, including failure results.
An unsupported capability is a named failure, not a passing skip.

## ScopeObservation

| Field | Meaning |
|-------|---------|
| `invocation` | Installed entry point, fixture root, arguments, and unique report paths |
| `process` | Actual exit code, stdout, and stderr |
| `evidence` | Actual scope counts, parsed count, analyzed paths, findings, and selection messages |

Store related evidence as a grouped record, not a long method signature.
The actual report supplies `analyzed_files` and finding identities.
Parsed logging supplies the parsed-file count.
Completed detector traces can supply analyzed paths when an input error prevents a report.

`gate_scope` contains the discovered-file and filtered-finding counts only.
Neither count identifies the selection mode or reason.
An early failure can leave counts or reports unavailable.
Represent that absence explicitly.

A valid empty-scope observation contains zero scope counts and a successful baseline comparison.
The installed CLI does not write a report on that early return.
The test must verify that no stale report exists.

## ScopeCase

| Field | Meaning |
|-------|---------|
| `case_id` | T01 through T16 plus a descriptive variant name |
| `history` | Fixture-local common, base, and candidate revisions |
| `file_states` | Committed, staged, unstaged, untracked, removed, or renamed fixture paths |
| `expected` | Independent expected paths, counts, findings, and exit result |
| `observed` | `ScopeObservation` or `GuardrailResult` from the real execution |

Known weak assertions use the finding identity `weak_is_not_none`.
The corresponding settings control is `weak_assert_not_none`.
Use stable fixture source lines and local baseline records.
Do not derive expected selection by duplicating the analyzer's resolver.

## State Transitions

### Guardrail

1. Identify the six required input paths.
2. Attempt each independent read.
3. Validate available settings, baseline, and CI text.
4. Decode the live contract.
5. Check each available active guide procedure.
6. Report measured progress and all named failures.

Any required read, decoding, or comparison failure makes the final result fail.
Completed independent checks remain visible in the failure report.

### Operator candidate

1. Run applicable local checks before the local commit.
2. Commit all intended tests and relevant inputs.
3. Confirm that relevant working-tree content matches the intended candidate.
4. Fetch and resolve the intended base.
5. Run the direct guard preflight.
6. Run the installed analyzer with the required scope controls.
7. Proceed only after zero new findings and all applicable checks pass.

A candidate or base change invalidates earlier affected evidence.
No pre-commit mechanism changes the installed endpoint comparison.

### Fixture

1. Create an isolated repository and valid local inputs.
2. Record known local revisions and references.
3. Apply one controlled state change.
4. Run the unchanged installed analyzer with unique output paths.
5. Compare actual evidence with explicit expectations.
6. Remove fixture state through normal pytest temporary-directory cleanup.

Fixture mutations never target the real repository, its baseline, or its settings.
