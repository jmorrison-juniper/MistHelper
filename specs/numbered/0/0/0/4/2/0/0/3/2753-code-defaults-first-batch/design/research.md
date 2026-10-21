# Research: Code Defaults First Batch

## Evidence Boundary

The issue assessment defines the five-file batch and historical counts.
Read the [specification](../spec.md) for the exact source, test, and ownership boundaries.
The current source revision during planning is `5bfadf9cb`.
All eight assessment test modules exist. No current open pull request overlaps the five source files.
Ownership must be checked again immediately before implementation.

No current full inventory or accepted high-severity baseline was produced.
No live service was contacted.

### Implementation Recheck

Before source edits, the complete paginated GitHub REST results listed 11 open pull requests and
553 file records. No file overlapped the five source modules, eight assessment test modules, or
planned scanner and test packages. The worktree had only the parent-authored feature directory
untracked. The source revision at this recheck was `5bfadf9cb`.

The approved file manifest is the five source modules and eight unit modules in `spec.md`, the
five modules in `src/foundation/support/code_defaults/`, four modules in
`tests/integration/helpers/code_defaults/`, this feature's design artifacts, and one unique
issue-specific changelog fragment. No other source file is approved.

Python 3.13.13 was present. `scripts/bootstrap_worktree.py` created `.venv`, installed
`requirements.txt` and `requirements-dev.txt`, downloaded Chromium, and found zero corrupt
package installs across 162 package records. The Python prerequisite script is absent from this
worktree. The PowerShell prerequisite command cannot run because `pwsh` is absent. The checked
requirements checklist has 16 items, all checked.

Before edits, the five source modules had 10, 73, 6, 27, and 1 top-level function or class
declarations in assessment order. The count excludes declarations nested in classes. Keep repairs
inside the listed files and do not add unrelated declarations or move modules.

### Historical Candidate Dispositions

The assessment section 8 manifest has 59 historical high-severity review targets. It lists
18 AP migration, 17 zone analyzer, 10 CSV comparator, 9 address utility, and 5 organization
migration candidates. These counts are historical only. The exact manifest and current
dispositions will be recorded after the scanner and source review run against the current tree.

### Reconciled First-Batch Manifest

The source review mapped every assessment section 8 high-severity row by its original line and
input. Three AP candidates were confirmed defects and repaired: response data at lines 1134 and
1258, and the selected profile ID at line 1216. The profile and site response fallback now
requires a successful response with a list of objects. It accepts a valid empty list. The profile
picker now rejects absent, blank, whitespace-only, and non-string IDs before migration begins.

The remaining AP rows at lines 448, 567, 605, 620, 624, 1669, 1670, 1842, and 1994 use collections
that the backup or operation already validates, or represent a permitted empty result. Rows at
1423, 1425, and 1426 use required backup fields that the validator checks. Rows at 1291 and 1293
are checked before backup use. Row 1263 is a site identifier owned by #2863 and remains unchanged.

The 17 zone rows at lines 251, 922, 972, 992, 1009, 1031, 1058, 1219, 1221, 1222, 1285, 1325,
1327, 1329, 1330, 1343, and 1436 are consumed from analyzer-produced maps or populate report
columns. Empty analyzer maps represent valid zero results. Zone IDs, map IDs, timestamps, and
duration fields remain report values. The existing empty-input and empty-export tests preserve
these contracts. No zone source repair was justified.

The ten CSV rows at lines 326 and 327 are optional mismatch columns. Rows 586, 647, and 758 use
serials that the lookup builder and comparison workflow validate or skip when blank. Rows 655
and 913 are optional address columns. Rows 941 and 963 populate failure-report metadata. Row
1393 is a report model field. Existing tests cover blank serials, optional address columns,
environment defaults, and failure records. No CSV source repair was justified.

The nine address rows include lines 95, 105, 395, 405, 505, 506, 1007, and 1071. The assessment
lists line 405 twice. The skip-list fields permit blank components. Parser results may contain
empty fields. The comparison boundary rejects empty required fields before scoring, while line 2
remains optional. Place-type and descriptive tiebreak data remain optional. The standalone
similarity helper keeps its documented empty-versus-empty result. The new comparison-boundary
test proves that missing primary street data does not match. No address source repair was justified.

The five organization rows at lines 177, 512, 525, 597, and 654 include optional listing or
network sections, the #2863 source organization identifier, and the created-object ID repair
already delivered by #4310. Existing tests prove failure rows, no blank mapping, and retained
results. No organization source repair was justified.

The current working-tree scan selected and parsed all five files. It found 197 candidates:
70 already validated, 56 valid optional, 66 display-only, and 5 excluded by #2863 ownership.
The accepted high-severity total is zero. This is a reviewed current scanner result, not the
historical total of 59. A separate repository-wide scan found 2,409 candidates across 1,058
tracked Python files, with zero parse failures. Its 2,212 outside-batch candidates do not change
the accepted scope.

The current five-file classification totals by source are:

| Source | Already validated | Valid optional | Display only | Excluded ownership | Total |
| --- | ---: | ---: | ---: | ---: | ---: |
| AP profile migration | 14 | 1 | 3 | 2 | 20 |
| Zone analyzer | 24 | 28 | 30 | 0 | 82 |
| CSV comparator | 14 | 10 | 23 | 2 | 49 |
| Address utilities | 16 | 11 | 8 | 0 | 35 |
| Organization migration | 2 | 6 | 2 | 1 | 11 |
| **Total** | **70** | **56** | **66** | **5** | **197** |

Every current candidate has a stable identity and a separate baseline disposition. The policy
also requires a disposition for a new low-severity candidate. A new high-severity identity fails
before that review check, even when another high-severity identity disappears. The five excluded
identities are site or organization identifiers owned by #2863.

The complete implementation manifest remains the five source files, eight specified unit test
files, the scanner package, its four test files, these design artifacts, and one issue-specific
changelog fragment. The new tests use temporary Git repositories or controlled API responses.
They make no cloud request.

## Decision 1: Validate at the Consumption Boundary

**Decision**: Determine whether a value is required from its consumer, producer, and existing input contract.
Validate before selection, comparison, remapping, path generation, or required collection consumption.

**Rationale**: An empty default is a review candidate, not proof of a defect.
AP migration already validates planned record shape and nonblank fields before some downstream accesses.
Zone row flags use analysis maps, while several zone fields are export columns.
CSV customer variables currently supply mismatch columns.
Address utilities intentionally permit an optional second address line.
Organization network sections and listing arguments can be optional.

**Alternatives considered**: Removing every empty default would reject valid optional inputs.
Treating all defaults as safe would preserve false successes.
Classify each use and preserve evidence for safe cases.

## Decision 2: Preserve Existing Repair and Error Conventions

**Decision**: Preserve the created-object identity failure from #4310.
Use existing domain errors or explicit failed records for new required-input failures.
Keep existing public names and change directly related tests with each repair.

**Rationale**: Organization migration already raises for absent created-object identities and records a failed result without a mapping.
AP backup validation already uses field-specific errors.
Generic blank replacements would weaken those contracts.

**Alternatives considered**: A shared validation framework or new global error hierarchy would expand the bounded change.
Adding compatibility wrappers would violate repository refactoring rules.

## Decision 3: Commit a Stable Scanner and Reviewed Policy

**Decision**: Discover tracked source files through Git and inspect the five assessment shapes with the standard syntax parser.
Combine deterministic syntactic candidate discovery with reviewed consumer classifications.
The baseline stores scope, criterion version, revision, stable identity, disposition, and evidence.

**Rationale**: Literal syntax alone cannot distinguish a display label from a selector.
The assessment source exists only in another session's folder and is not available to this worktree.
Do not claim to reproduce its counts without a committed scanner.

**Alternatives considered**: A regular-expression scan cannot reliably distinguish nested uses.
Recreating a repository-wide ownership allocation would violate scope.
An aggregate count alone could let one removed candidate hide a new one.

## Decision 4: Bound Enforcement, Not Discovery

**Decision**: The inventory can report tracked non-test source candidates across the repository.
Enforce the accepted baseline only for the five-file scope and explicitly accepted high-severity candidates.
Report other findings as outside this batch, without changing their ownership or claiming their count as current assessment evidence.
Unclassified candidates inside the five-file scope prevent acceptance.

**Rationale**: A stable scanner must distinguish discovery from permission to repair.
The 99 deferred upgrade-input candidates and other ownership ambiguity remain unresolved.

**Alternatives considered**: Enforcing an unreviewed repository-wide baseline would absorb work without authorization.
Ignoring unclassified in-scope candidates could conceal a regression.

## Decision 5: Use Compliant Package Parents

**Decision**: Use `src/foundation/support/code_defaults/` and `tests/integration/helpers/code_defaults/`.
Keep the regression guard collected as a normal pytest test.

**Rationale**: The usual script and guardrail folders already exceed five children.
The selected parents can accept one package without increasing existing excess.
The new source package has five children. Its test package has four.

**Alternatives considered**: A new root-level scan script or direct guardrail module would increase structural debt.
Placing feature tooling in an unrelated existing module would obscure its purpose.

## Tooling Findings

The active plan and checklist templates resolve to `.specify/templates/`.
The planning setup command cannot run because `pwsh` is absent.
The existing feature directory and template were resolved directly without changing `.specify/feature.json`.
`ste-linter` is also absent. No automated writing score is claimed.
These limitations do not justify modifying repository tools, templates, or dependency manifests.
