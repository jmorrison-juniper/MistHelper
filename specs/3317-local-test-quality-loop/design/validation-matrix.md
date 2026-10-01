# Validation Matrix: Local Test-Quality Loop

**Specification**: [spec.md](../spec.md)

**Status**: Scope and guidance cases pass on the authorized base. Publication and exact-main proof remain pending.

## Fixture Rules

Use the unchanged installed analyzer in isolated local Git repositories.
Use the active Python interpreter and installed module entry point.
Do not replace the resolver, detector, or CLI output.

Use fixture-local copies of settings and baseline inputs.
An empty valid baseline list is sufficient for most cases.
Do not edit repository settings, baseline, or requirements.
Do not import product modules or require network access.

Create fixture references locally to represent fetched intended bases.
Never fetch a remote inside a scope fixture.
Control rename behavior only inside the fixture's Git configuration.
Never change real repository or global Git configuration.

Run each observation in a fresh process with a 30-second timeout.
Use `--log-level DEBUG` and unique fixture-local `--report` and `--summary` paths.
Those diagnostic controls do not change selection.
Do not add `--roots` or disable rules except in explicit invalid-control cases.

## Common Witnesses

Ordinary fixtures contain these two committed tests:

| Path | Initial content | Purpose |
|------|-----------------|---------|
| `tests/test_changed.py` | Strong assertion with no expected finding | Controlled candidate path |
| `tests/test_witness.py` | Known non-None weak assertion | Unchanged full-suite witness |

The weak expression is `assert result is not None`.
Its emitted identity is `weak_is_not_none`.
The settings control name is `weak_assert_not_none`.
Keep both templates' assertion lines stable.

The common empty baseline accepts no finding.
A full scan of these two files therefore expects two analyzed paths and one new finding.
Changed-scope cases expect only their explicitly named candidate paths.
The unchanged weak witness must remain excluded unless a trigger or full-suite command includes it.

Use separate local baseline fixtures for accepted-finding controls.
Create accepted identities before the comparison base commit.
Do not change the baseline between compared commits unless the case tests its automatic trigger.

The fixture also contains a local JSON subject and genuine input-boundary assertions.
These source signatures give full-mode detectors applicable scope without suppressing rules.
The known weak assertion remains at line 3.
No product module or network service participates.

## Required Observation Record

Record these actual results for every analyzer invocation:

- Case identifier and variant.
- Fixture base and candidate revisions.
- Actual argument vector and exit result.
- Stdout scope counts when the CLI emits them.
- Parsed-file count from installed logging when available.
- Exact analyzed paths from the report or completed detector traces.
- Finding identities and selection messages.
- Report existence or an explicit unavailable reason.

Use expected sets and counts defined by the fixture, not a copied resolver.
For ordinary valid scans, assert discovered, parsed, and analyzed counts separately.
Do not infer an analyzed path set from a count alone.

A valid empty scope expects zero scope counts and no report.
The CLI returns before parsing any test.
Record that observed early-return condition explicitly.
Do not reuse another observation's report.

Early input errors can prevent scope counts or reports.
Record unavailable fields as unavailable.
If completed detector traces exist, count those actual analyzed paths.
Do not replace unavailable error evidence with invented zero values.

## T01-T04: Names and Changed Paths

| Group | Positive or inclusion evidence | Negative or exclusion evidence | Expected key results |
|-------|--------------------------------|--------------------------------|----------------------|
| T01 | Add and modify prefix and suffix test names. Use one known weak finding per selected file. | Add and modify lookalike names, including `testlookalike.py` and `sample_tests.py`. Keep the unchanged weak witness excluded. | One selected weak test gives 1 discovered, 1 parsed, 1 analyzed, 1 new finding, and exit 1. A strong selected control gives exit 0. Lookalikes give a valid empty scope. |
| T02 | Delete a committed recognized test and compare against its base. | Confirm that neither the deleted path nor unchanged witness enters analysis. | Zero selected files, zero scope findings, exit 0, and no report. Never attempt to analyze the removed file. |
| T03 | Rename a weak test to another recognized prefix or suffix name. Rename a non-test to a recognized test. | Rename a recognized test to a non-test name. Confirm that old nonexistent names never enter analysis. | Recognized destinations give one analyzed destination and one new finding. Non-test destinations give a valid empty scope. |
| T04 | Commit an unrelated document change with valid required analyzer inputs. | Keep known weak tests unchanged and outside scope. Pair with a missing-baseline error. | Valid inputs give zero scope counts, exit 0, and no report. The invalid required baseline gives exit 2, not a valid empty result. |

Each naming variant uses an independently identified fixture path.
Do not claim that any Python file containing `test_*` functions matches the filename contract.
Use exact renames to obtain reliable rename detection.
Record observed old and new changed names where Git supplies both.

## T05-T08: All Four Trigger Paths

For each group, test addition, modification, deletion, and rename.
Use fixture histories that make the exact live trigger path appear in the endpoint difference.
Derive explicit controls from the live CI command.

The implemented matrix covers recognized incoming renames as an additional variant.
Those cases retain fixture-local `diff.renames=true`.
Outgoing removal variants use fixture-local `diff.renames=false` so the endpoint difference names the old trigger.
This setting does not claim that every default recognized outgoing rename names both paths.
Trigger behavior requires the exact path to appear in the actual endpoint difference.
No real repository or global Git setting changes.

| Group | Trigger | Positive evidence | Negative or failure evidence |
|-------|---------|-------------------|------------------------------|
| T05 | `.github/workflows/ci.yml` | Each applicable change form includes both ordinary test paths and the unchanged weak witness. | Omit or change this explicit control in the actual invocation. The same trigger-only history then produces a valid empty scope. The guide guard must reject that omission. |
| T06 | `requirements-dev.txt` | Each applicable change form includes both ordinary test paths and the unchanged weak witness. | Omit or change this explicit control. Confirm exclusion under the same history and rejection by the guide guard. |
| T07 | `.github/test-quality-config.toml` | Each applicable change form triggers the full suite automatically. Addition and modification retain valid settings. Deletion and rename exercise documented defaults. | An unrelated-only comparison does not trigger the full suite. Malformed or unreadable settings fail before selection and cannot prove a successful scan. The guide guard rejects a missing required settings file. |
| T08 | `.github/test-quality-baseline.json` | Addition and valid modification include the unchanged weak witness automatically. A valid whitespace-only baseline modification can prove path-based triggering. | Deletion or rename leaves a required comparator missing. Expect exit 2 after actual full-suite scanning, not a passing empty result. |

For successful trigger observations, expect:

- Two discovered test files.
- Two parsed and analyzed paths.
- The unchanged witness's `weak_is_not_none` finding.
- One new finding against the local empty baseline.
- Exit 1.
- A stderr explanation naming the trigger.

Use an accepted-finding variant to prove a full scan can return exit 0.
Its analyzed witness remains present even when the baseline accepts its finding.
Do not change expected scope to obtain the positive exit result.

### Required baseline removal detail

The analyzer loads settings and resolves scope before it evaluates the baseline.
A baseline deletion or rename can therefore select and analyze the full suite before exit 2.
Assert the actual trigger message, parsed count, and completed weak-detector traces.
The JSON report and `gate_scope` line can remain unavailable on that error.

Add a paired observation with a restored fixture-local baseline in the working tree.
Keep the same committed deletion or rename history.
That observation must produce the full two-path report and known witness finding.
Label the restored-input case as controlled dirty fixture evidence, not a clean pre-push candidate.
It proves committed path selection and current input reads without weakening required baseline safety.

## T09-T11: Modes and References

| Group | Positive evidence | Negative or exclusion evidence | Expected key results |
|-------|-------------------|--------------------------------|----------------------|
| T09 | Run without changed-scope controls on unchanged ordinary tests. Repeat with a local accepted baseline. | Add `--changed-from` against an equal candidate reference. Confirm that the resulting empty scope cannot represent the full-suite procedure. | Full mode gives 2 parsed and analyzed paths. Empty baseline gives 1 new finding and exit 1. Accepted baseline gives zero new findings and exit 0. |
| T10 | Compare two known valid bases, including divergent history. | Use an alternate base that excludes the intended finding. Confirm that the guide rejects a substituted base expression. | The divergent intended endpoint comparison includes one weak shared test. The common-base comparison produces a valid empty scope. |
| T11 | Use a known resolving intended reference. | Use an unknown reference, empty value, or option-like revision. Use a mismatched documented fetch destination. | Valid references give their declared scope. Unresolved or invalid scope controls give exit 2. A missing scope line is not zero-file success. |

### Divergent-history fixture

Create three local revisions:

1. Common revision A contains weak `tests/test_shared.py`.
2. Intended base B descends from A and strengthens that test.
3. Candidate H descends from A and changes only an unrelated document.

For B to H, the endpoint difference includes `tests/test_shared.py`.
H still contains its weak assertion.
Expect one selected, parsed, and analyzed file, one new finding, and exit 1.

For A to H, no test path changes.
Expect a valid empty scope and exit 0.
Merge-base selection for B and H would use A and exclude the test.
The installed B-to-H observation must therefore distinguish the two semantics.
Do not invoke a replacement merge-base selector as the required check.

## T12-T14: Local File States

| Group | Before local commit | After local commit or selected-content change | Expected key results |
|-------|---------------------|----------------------------------------------|----------------------|
| T12 | Stage a new or modified weak test while the committed endpoint difference contains no test change. | Commit the weak test. Then stage a strong edit to that already selected path. | Before commit, scope is empty. After commit, one weak selected test returns exit 1. A selected current strong edit produces one analyzed path with zero findings. |
| T13 | Leave a tracked weak edit unstaged on a path absent from the committed test difference. | Commit it, then change only its working-tree assertion. Include different index and working-tree contents. | Unselected dirty-only paths remain excluded. Selected paths follow current working-tree content, not the index or committed source. |
| T14 | Create an untracked recognized weak test. | Add and commit that test. | Before commit, scope is empty. After commit, its one analyzed path and finding return exit 1. |

In T13, stage a strong version but leave a weak version in the working tree.
The installed analyzer must report the weak finding.
Then leave a strong current version with the same candidate `HEAD`.
The same selected path must produce zero findings.
These observations distinguish content reads from path selection.

An optional selected-path removal variant can prove the existing-file requirement.
It must not count as a clean operator candidate.
Each guide must state the clean committed-candidate requirement.

## T15: Required Input Safety and Defaults

### Direct guard

Test each of the six required inputs independently:

- Missing file.
- A directory in place of the required file.
- Named read failure where the platform permits a controlled permission case.

Directory replacement gives a deterministic unreadable-file case across platforms.
It avoids permission-dependent skips.
Use malformed workflow, TOML, and JSON variants as additional validation failures.

Assert the failed path and actual partial read, validation, guide, and path counts.
Never assert a hard-coded four-input total.
Readable empty TOML remains parseable for the new preflight.
Existing repository settings tests retain their separate structural checks.

### Installed analyzer

| Variant | Required expectation |
|---------|----------------------|
| Missing settings and valid baseline | Defaults apply. A controlled unrelated-only history can return a valid empty scope. |
| Empty settings and valid baseline | Defaults apply with the installed explanatory log. |
| Unreadable settings | Exit 2 with a named IO error |
| Malformed settings | Exit 2 with a named config error |
| Missing, unreadable, or malformed baseline | Exit 2 even when zero tests enter selection |
| Disabled baseline with an empty value | Exit 2 in gate mode |
| `--changed-from` with `--roots` | Exit 2 |
| `--changed-from` with baseline-writing or pruning controls | Exit 2 |

Use actual unreadable fixture paths for analyzer subprocess cases.
Do not mock analyzer reads or substitute expected output.
An error observation must identify unavailable scan evidence honestly.
The documentation must distinguish guard rejection from analyzer defaults.

## T16: Active Command Drift

Run these mutations for every guide where they apply:

- Remove the active command or active label.
- Put a valid command only in a comment, another section, or unused example.
- Replace the executable with an obsolete entry point.
- Remove or change `--gate`, settings, baseline, or base controls.
- Omit either explicit trigger or replace it with another path.
- Add a conflicting duplicate control before or after a correct value.
- Add extra roots, disabled rules, baseline writes, or unsupported shell constructs.
- Quote the base as a literal or change its fetch destination.
- Use another shell's assignment syntax or an unquoted PowerShell command value.
- Add changed-scope controls to the active full-suite command.

Positive cases change static quoting, option order, RTK prefixes, and supported continuations.
They must retain the same semantic controls.
Identical singleton repeats can normalize.
Duplicate explicit trigger values fail.

Add a third trigger to the live CI fixture and leave every guide unchanged.
The guard must fail using three decoded explicit paths, not a cached two-path list.
Update all active fixture commands to match and confirm success.
Keep six required input files in both observations.

Pair similar-looking command drift with real installed analyzer observations.
Omitting an explicit trigger must exclude the unchanged witness.
Disabling `weak_is_not_none` must alter the finding result and fail the guidance contract.
Extra roots combined with changed-scope controls must return exit 2.
Text-only guard mutations do not replace those behavioral pairs.

## Coverage Completion Rule

Assign T01-T16 identifiers to parametrized pytest case names.
Print measured observation summaries with each case identifier.
The parent must account for every required group and applicable variant.
A skipped, uncollected, timed-out, or unsupported case leaves evidence incomplete.

Negative analyzer exits are expected results inside passing tests.
Unexpected analyzer output or a wrong path set must fail the pytest assertion.
No requirement permits a baseline update to conceal a new finding.

## Measured Local Results

| Evidence | Actual result |
|----------|---------------|
| Input accounting red | 24 expected failures before input reading existed |
| Input accounting green | 24 passed |
| Semantic normalization red | 12 expected failures before live CI decoding existed |
| Literal-preservation red | 9 failed and 3 passed before correction |
| Literal-preservation green | 12 passed |
| Guidance fixtures | 396 passed with only the actual live class excluded |
| Actual live guides before edits | 1 failed, naming all three omitted active procedures |
| Actual live guides after edits | 1 passed |
| Scope matrix | 82 passed with 124 genuine analyzer invocations |
| New package and unchanged ratchet | 493 passed, 0 skipped |
| Affected document guards | 142 passed, 0 skipped |
| Preliminary explicit-root analyzer | 2 files checked, 0 findings, 0 new findings, exit 0 |
| Parent shell-profile regression proof | 21 failed before the correction, then 21 passed |
| Final new package and unchanged ratchet | 514 passed, 0 skipped |
| Guard and fixture coverage | 98.22 percent across 841 statements |
| Final document and link guards | 161 passed, 1 existing pull-request-only skip |
| Configured full-suite analyzer | 949 files checked, 725 findings checked, 0 new findings |

The live red report measured six reads, three validations, and three completed guide decisions.
The green report measured six reads, six validations, and three completed guide decisions.
Both decoded two explicit, two automatic, and four effective path controls.
The fixture CI-drift pair measured three explicit and five effective controls.

The preliminary root result does not prove configured committed scope.
The parent retains the clean candidate commit, fetched intended base, and final configured ratchet.
Native PowerShell execution and dictionary-backed STE vocabulary coverage remain unavailable.
The existing changelog diff guard skips because a local run has no pull-request event.
No new guard or required offline case skips.

The authorized rebase uses devtools 0.6.0 without a feature-owned dependency change.
All 514 ratchet cases pass again and retain 98.22 percent coverage.
The exact committed comparison checks two files and finds zero new findings.
The configured full-suite check reads 994 files and finds zero new findings.
