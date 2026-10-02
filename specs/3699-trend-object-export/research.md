# Research: Export documented trend objects

**Issue**: [#3699](https://github.com/jmorrison-juniper/MistHelper/issues/3699)

**Preparation base**: `77699c7483c1e90df14f9650ed90e98e512bee97`

## Ownership and Scope

The authenticated account is `jmorrison-juniper`.
The complete issue initially had no assignee, comments, or `in-progress` label.
Two complete open-PR inventories contained zero PRs.
The completed #3335 claim still reserved both shared paths.
An absent open PR did not release that reservation.

The [private preparation claim](https://github.com/jmorrison-juniper/MistHelper/issues/3699#issuecomment-5953810192) records both session identifiers and position 44.
The parent owns publication.
No full verified-main publication grant exists for this feature.

The parent later approved the exact support package and both concrete behavior decisions.
The completed owner publicly released only the exporter and its existing unit module in claim `5936510347`.
This owner's claim recorded the release before shared source edits.
The claim also reserves both private test support files.
All metadata, catalog, key, menu, generator, dependency, and policy inputs remain read-only.

## Actual SDK Evidence

**Decision**: Use native SDK `0.64.0` responses and actual endpoint functions.

**Rationale**: A mock list does not prove export of either documented object.
The SDK decodes both literal documents correctly but `get_all` discards them.

**Alternatives considered**: Change the SDK constraint, synthesize `results`, or test only `_normalize`.
Each alternative misses the actual response boundary or changes the contract.

The own controlled probe invoked each actual trend function through `mist_get`.
It returned a real `requests.Response` decoded by the actual `APIResponse`.
The actual `_run` and normalization executed with a controlled final output callback.
The probe supplied required arguments directly.
The later regression tests must also execute the actual menu and identifier prompts.

| Operation | Status | Next link | Decoded equality | Endpoint calls | `get_all` records | Normalized records | Output callbacks |
| --- | ---: | --- | --- | ---: | ---: | ---: | ---: |
| `getSiteSleSummaryTrend` | 200 | None | Exact document | 1 | 0 | 1 | 0 |
| `getSiteSleClassifierSummaryTrend` | 200 | None | Exact document | 1 | 0 | 1 | 0 |

The global `requests.Session.request` guard recorded zero calls.
The probe closed its owned session and removed its temporary directory.
No credential or live Mist request was necessary.

## Status and Body Boundary

**Decision**: Reject unsuccessful or unusable status before shape selection.

**Rationale**: A native HTTP `403` response can contain a nonempty dictionary.
The new object branch must not export it as data.

**Alternatives considered**: Existing helpers that default missing status to `200`, or tests of a payload's `error` string.
Neither alternative establishes actual HTTP success.
Successful metrics may contain legitimate `error` fields.

`ResponseIntegrityChecker` already detects nonempty malformed bodies that the SDK silently converts to `{}`.
Its diagnostics print body length, not body content.
Reuse that actual helper without changing its implementation.
An empty wire body needs an explicit decision because that helper treats it as no parse evidence.

The SDK constructor logs HTTP errors but returns their decoded bodies.
The SDK can also return `APIResponse(None, url)` without a status.
The execution boundary must distinguish these failures from a successful empty response.

## Concrete Later-Page Limit

**Decision**: Report the native limit before replacing collection behavior.

**Rationale**: The actual SDK does not validate each page status.
The local probe supplied one list record and a real next-page HTTP `403` object.
`get_all` returned the first record followed by the string `"error"`.
The existing flattener then retained the first record.
A complete-looking partial export can therefore survive a later-page refusal.

The probe made exactly one native next-page call.
The parent received this concrete scope report.
A checked traversal through actual `mistapi.get_next` received explicit parent approval.
Successful link construction, record order, and call counts must remain unchanged.
No header-total semantics or SDK modification is proposed.

## Concrete Empty-Array Limit

**Decision**: Report the existing empty-array convention instead of changing output helpers.

**Rationale**: The existing flattener treats an empty list as a list of dictionaries.
It expands zero elements and emits no field.
The literal summary's `classifiers: []` therefore has no flattened field.
Nonempty classifier and sample arrays retain their values through the established expansion and joining rules.

The parent explicitly accepted this convention.
The repair changes no helper, key, output schema, or default context.
Canonical CSV and SQLite tests must inspect actual selected output.
No writer result may be replaced by artificial success.

## Own Environment and Immutable Quality Baseline

The required bootstrap command failed before requirement installation:

```text
rtk proxy python3.13 scripts/bootstrap_worktree.py
subprocess.CalledProcessError: Command '[.../.venv/bin/python3.13, -m, ensurepip, --upgrade, --default-pip]' died with <Signals.SIGABRT: 6>.
```

This is the known macOS [#3701](https://github.com/jmorrison-juniper/MistHelper/issues/3701) setup limit.
It is not a passing bootstrap result.
Only the own ignored `.venv` received the authorized UV recovery:

```bash
rtk proxy env UV_LINK_MODE=copy UV_NATIVE_TLS=1 UV_SYSTEM_CERTS=1 uv venv .venv --python python3.13 --seed --clear
rtk proxy env UV_LINK_MODE=copy UV_NATIVE_TLS=1 UV_SYSTEM_CERTS=1 uv pip install --python .venv/bin/python -r requirements.txt -r requirements-dev.txt
```

Both recovery commands passed.
The environment contains Python `3.13.13`, SDK `0.64.0`, and 160 distributions.
No borrowed environment, token, audit lock, or STE dictionary was used.
No dependency manifest changed.

The required-input preflight passed before the initial analyzer:

```text
inputs_attempted=6 input_reads=6 input_validations=6 guide_reads=3 guide_checks=3
```

The complete unchanged-base ratchet passed:

```text
gate_scope: 1003 files checked, 725 findings checked
48 configured skips, 0 parse errors, 0 new findings
```

The immutable JSON report remains in the own session artifact directory.
Candidate comparisons must read source-dependent applicability, not just changed test filenames.

## SpecKit Procedure and Capability Limits

The active specification, plan, tasks, analysis, and constitution sources were read.
The four feature files use the active template structure and explicit paths.
PowerShell is unavailable.
The configured hooks request branch changes, shared feature-state changes, and automatic commits.
Those actions conflict with this app-managed local-only reservation.
No hook, shared `.specify` state, or governance edit occurred.

The licensed STE dictionary remains unavailable.
Do not borrow another worktree's dictionary or claim complete dictionary coverage.
The normal macOS audit resolver can also abort during `ensurepip`.
If that occurs, retain the failure and use the complete own hashed runtime audit.
Count every audited package and state the Git-only development-tool limitation.

## Native Red and Green Evidence

Four unchanged-source cases failed at the required real output callback.
They cover both literal documents with obsolete SDK attributes present and absent.
Each native response has HTTP `200`, no next link, and exact decoded equality.
Each journey makes one site lookup and one actual endpoint call.
All four produced zero output callbacks.
The red JUnit report remains in the own session artifacts.

The same four assertions pass after the semantic reader repair.
The native suite passes 785 cases.
The complete affected suite passes 1,548 cases without failures or skipped cases.
The source reader measures 100 percent coverage over 82 statements and 34 branches before the final equivalent Boolean-status refinement.
The final verification repeats the affected coverage after that refinement.

The first output run exposed four resource warnings from the owned SQLite inspection connection.
The test now explicitly closes that connection.
All 26 selected-output cases pass with `ResourceWarning` treated as an error.
No production writer or database cleanup scope changed.

Repeated SQLite writes preserve the existing snapshot replacement.
The auto-increment strategy clears the old snapshot before inserting the new snapshot.
Two writes therefore retain one record with internal identifier `2`.
Both canonical documents and both rich documents succeed without added context or a key change.
Existing natural-key and composite-key regressions remain unchanged.

## Immutable Metadata and Quality Evidence

All 17 protected input hashes match the preparation base.
The initial reader design kept 12 unrelated exporter method ASTs unchanged.
The later approved typed-caller migration changes only real contract arguments in the remaining caller methods.
All five selector and resolver method ASTs remain unchanged.
The normalization body migrates exactly, without an alias or compatibility wrapper.
The complete operation metadata AST remains unchanged.

```text
Metadata AST SHA-256: 4c2bd03cd599c95ecd5fd49166cfaed3974f7e74d903f0bc7e1c20471bcbcc17
PK file SHA-256: 50fa567ddf5a2e6b38ad33153c8a0461f10898f9f5d4ce125d1316e72ad83776
```

The first full candidate ratchet reported four missing HTTP failure obligations in two new modules.
Those modules used an external failure fixture that the status-context analyzer could not prove.
Each module now directly executes native HTTP `403` and `503` with literal status parameters.
No source, test, baseline, exclusion, or threshold was hidden.

The complete ratchet then passes for 1,007 discovered files and 725 findings, with zero new findings.
All 725 complete finding identities match the immutable full-base report.
The four new native modules also pass explicit `--include-mist-api` analysis with zero findings.
All four appear in `analyzed_files`.
Its two omitted-root entries describe deliberate scoped roots, not omitted feature modules.

The standard `pip-audit -r requirements.txt` command also aborts during macOS `ensurepip`.
It is not a clean standard audit.
The own UV resolver produced a complete hashed runtime lock.
The strict `--require-hashes --no-deps --disable-pip` audit checks all 105 runtime packages.
It reports zero advisories and zero skipped packages.
The Git-only development tool remains outside that runtime audit.

## Corrected Policy Ownership and Accepted Local Base

The first read-only API-map guard rejected four of 16 pages.
Its exact difference showed false trend references from menus 264-268.
The shared reader operation-name constant caused those edges.
The initial source-line explanation was incorrect.
No source padding, string concealment, generator exception, or false page regeneration occurred.

The parent approved a typed caller-policy refinement within the existing source reservation.
The SLE caller now owns the two explicit operation names.
Each real menu and run call passes a required `EndpointFamilyResponseContract`.
The data contract remains passive.
The generic reader owns actual I/O, status, integrity, and parsing.
It contains no operation-name lookup.
The exact normalizer migration remains unchanged.

The 294-case contract suite executes all 132 real SDK functions with each canonical input.
Only the two intended operations produce object output.
The global request and production-router guards record zero calls.
Both negative output guards still detect their intentional bypass.

The parent grants local refresh only on accepted main `7a4435bdf8ceff7e1dd527e4d2fd854e79542f37`.
Its accepted tree is `e93408930b7107dd0ca5f4beecfe3440fd812d2b`.
The exact page release is [public claim 5955903781](https://github.com/jmorrison-juniper/MistHelper/issues/3300#issuecomment-5955903781).
The accepted receipt is [PR #3730](https://github.com/jmorrison-juniper/MistHelper/pull/3730#issuecomment-5955489893).
The parent owns publication.
Issue #3314 and PR #3731 hold the current publication window.

The own worktree refresh preserves stash `9d96feb696df742bcda242ee4b439060168b873d`.
All 16 exact feature-file hashes match after the refresh.
Both unchanged generators run twice against the combined source.
Only two released interactive-safe pages change.
All 18 outputs and 1,477,279 bytes are identical after the second run.
The 16-page guard passes for 293 menus.
The accepted selective-cache counts and all 28 full definitions remain intact.
No unowned output changes.

The refreshed affected suite passes 1,812 cases without failures, warnings, or skips.
Combined scoped coverage is 98.32 percent.
The reader covers all 89 statements and all 34 branches.
The complete refreshed ratchet checks 1,008 files and retains the same 725 findings.
Explicit native analysis checks all four new modules with zero findings.
The exact CI mypy scope passes 667 source files.
Explicit test mypy passes eight files.
Full Ruff, Black, Bandit, complexity, dead-code, and documentation checks pass.
Pylint scores 9.83/10.
Documentation coverage is 99.6 percent across 13,232 definitions.
STE scores pass with the unchanged unavailable-dictionary limitation.
