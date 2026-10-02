# Implementation Plan: Selective Insight Definitions

**Branch**: `jmorrison-juniper-selective-insight-definitions` | **Date**: 2026-10-01 | **Spec**: [spec.md](spec.md)

**Input**: `specs/3300-selective-insight-definitions/spec.md`

**Base revision**: `ff3cc1bea8ab58026210a968ff1465f61c9fec78`

**Issue**: [#3300](https://github.com/jmorrison-juniper/MistHelper/issues/3300)

## Summary

Refresh only `insight_metrics` before the site, device, client, and organization insight exports.
Keep the existing exporter as the authority for discovery, cache age, normalization, output, and counts.
Add a selected entry that returns a result with the first failure.
Check HTTP status and the writer Boolean result before reporting an update.
Retain the existing empty fallback without letting it replace the first error or count another failure.

Use `InsightMetricsUtils.export_const_insight_metrics` for all four callers.
Change only the client wiring. Remove its unused direct exporter dependency.
Keep `export_all` dynamic and complete.

This step creates planning artifacts only. It does not implement, test, benchmark, commit, or publish the repair.

## Technical Context

**Language/Version**: Python 3.13+. This worktree already has Python 3.13.13 in `.venv`.

**Primary Dependencies**: Existing `mistapi>=0.64.0,<0.65`, `requests`, standard-library discovery, logging, and data records.
The installed SDK is `mistapi 0.64.0`. Do not change dependency manifests.

**Storage**: Existing `data/ConstInsightMetrics.csv` and its modification time.
Retain `DataExporter.write_with_format_selection` for configured backends.
Tests replace the writer with an offline CSV seam under `tmp_path`.
No schema, primary-key, store, or cache-policy changes apply.

**Testing**: Existing pytest, pytest-cov, and pytest-timeout.
Use two reserved test files for new evidence.
Use the existing focused baseline modules without edits.
Retain real SDK discovery, cache checks, normalization, and scope reading.

**Target Platform**: Existing Windows and Linux CLI paths, with local validation on macOS.
Use cross-platform path handling. Use ASCII logs.
No container or live service validation is authorized.

**Project Type**: Existing Python CLI export workflow with shared internal helpers and operator-visible CSV output.

**Performance Goals**: One request and one definition write for each successful stale selected refresh.
Fresh selected caches require zero requests and writes.
Each caller must achieve at least a 90% controlled median reduction across five matched offline pairs.

**Constraints**: Retain the strict `<24 hours` cache rule, output fields, ordered scopes, caller contracts, and full export coverage.
Retain first errors and HTTP status. Count a failed attempt once.
Use only the reserved implementation files during a later implementation step.

**Scale/Scope**: Four actual caller entries and 28 controlled baseline definitions.
The selected operation processes one definition. Full export retains SDK-driven coverage and parameter handling.
No design clarification remains. [research.md](research.md) records the decisions and alternatives.

## Constitution Check

The [constitution](../../.specify/memory/constitution.md) governs this design.
The initial and post-design checks use the same bounded scope.

| Gate | Initial check | Post-design check |
| --- | --- | --- |
| Structural limits | Narrow existing-class changes require the exceptions below. | The design adds no production module or package. New methods remain within function limits. |
| Class ownership | The existing exporter owns selected discovery and processing. | The result is a data record, not a forwarding service. No wrapper or compatibility shim applies. |
| Safety | Validate the selected name before import. Keep all tests offline. | No credentials, live APIs, stores, containers, or production files enter validation. |
| Output compatibility | Retain the existing cache, normalizer, scope reader, and writer. | The contract retains filenames, eight ordered fields, scopes, and empty-output behavior. |
| Observability | Add before-and-after action logs to each changed block. | Logs include selection, cache decision, status, counts, and first versus secondary failures. |
| Comments and language | Comment only non-obvious intent under the current instructions. | New prose, comments, and refresh messages obey the STE guide. Logs remain ASCII and secret-free. |
| Local gates and publication | This step has no executable changes or deployment. | Later implementation requires the configured local gates. Publication remains blocked. |

**Gate result**: The design passes with the bounded structural exceptions in Complexity Tracking.
No unjustified design violation or unresolved technical question remains.
Unavailable workflow tools are not successful validations.

### Existing structural debt

The inspected source has 56 exporter methods, 21 insight-helper methods, and 14 client-service methods.
The exporter initializer also assigns six instance attributes.
The selected result uses local counter snapshots. It does not add shared failure attributes.
Keep changes inside the existing semantic owners.
Do not repair their unrelated methods.

The inspected directories contain 48 export children, seven analytics children, and nine serial-client children.
The export test directory contains 45 children.
The reserved new test file adds one child there.
The analytics test edit changes an existing child.
Counts exclude hidden entries and `__pycache__`.

The existing `_determine_special_handling` signature and `_resolve_site_name` length also exceed function limits.
Both remain unchanged. Reading them does not authorize their repair.

**Separate remediation**: A later authorized change can divide existing oversized classes into cohesive owners under compliant packages.
It can move test groups into compliant subpackages and replace oversized signatures with configuration records.
This feature does not perform that redesign or create another issue for it.

## Project Structure

### Documentation for this feature

```text
specs/3300-selective-insight-definitions/
|-- spec.md                         # Existing specification, unchanged.
|-- checklists/requirements.md      # Existing checklist, unchanged.
|-- plan.md                         # Current planning output.
|-- research.md                     # Local findings and decisions.
|-- data-model.md                   # Cache, result, and output records.
|-- contracts/definition-refresh.md # Selected refresh and caller contracts.
`-- quickstart.md                   # Later validation guide.
```

Do not create `tasks.md` during this step.

### Reserved implementation files

```text
src/
|-- export/const_definitions_exporter.py
|-- analytics/insight_metrics_utils.py
`-- refactors/serial_cc/site_client_insights.py

tests/unit/
|-- export/test_selective_insight_definitions.py
`-- analytics/test_insight_metrics_utils.py

changelog.d/issue-3300-selective-insight-definitions.md
```

These paths are a later implementation boundary, not files to edit now.
The site, device, and organization caller files remain unchanged.

**Structure Decision**: Extend the existing exporter and helper in place.
Keep one result record in `const_definitions_exporter.py`.
Do not add a generic endpoint framework, wrapper module, selection registry, or dependency.

## Design Decisions

### Selected discovery and processing

1. Validate one public ASCII SDK module name.
2. Remove only its prior registration, if present.
3. Inspect only that module through `_inspect_module`.
4. Process its `EndpointConfig` through `_process_single_endpoint`.
5. Return and log a result for the current attempt.

Do not call `_discover_endpoints`, `_process_all_endpoints`, or `export_all` from the selected entry.
An invalid or unavailable selection returns failure without another definition request or cache access.
Full export retains its existing discovery loop and parameter dispatch.

### Result and failure treatment

`DefinitionRefreshResult` carries five fields.
They are the selected name, outcome, four counter differences, original HTTP failure status, and first error.
Its outcome is `fresh`, `updated`, or `failed`.
The result never infers success from a file or fallback.
The test seams measure actual requests, write attempts, and successful writes separately.

Return caught discovery and processing errors through the existing private method chain.
Full export ignores these new private return values and retains its public `None` return.
Do not add another counter owner.

Check HTTP `4xx` and HTTP `5xx` before unwrapping a response.
Preserve the response on the first HTTP exception.
Treat an SDK response without an HTTP status as a transport failure.
Check the writer Boolean in both normal and successful-empty paths.
Increment `endpoints_updated` only after primary write success.

Record and count the first expected fetch or output failure before the existing empty fallback.
Keep the fallback to preserve empty-output behavior.
Contain expected fallback failures and log them as secondary errors.
Return the first error without a second failure increment.
Keep unexpected programming faults visible.

### Shared helper and caller compatibility

The helper selects `insight_metrics` and keeps its `None` return.
It reports a failed result before considering file availability.
Only a `fresh` or `updated` result can permit an availability message.
The selected file can still be absent in a configured non-CSV mode.
Keep that distinction between primary output success and CSV availability.

The client service uses `deps.InsightMetricsUtils.export_const_insight_metrics()`.
Its resolver no longer exposes the direct exporter.
No changes apply to selection prompts, operation banners, scope loading, insight collection, or empty output.
An old file that survives failure retains existing read behavior, but it cannot make the refresh report success.

### Validation and performance

Record four failing caller tests before source changes.
Mock only external API responses, output backends, cache time, and necessary runtime dependencies.
Do not mock the method under test, selected processing, normalization, or the shared helper.

Use the actual four refresh entries for timing.
Run at least five trials per caller before implementation and five matching trials afterward.
Use a 50-millisecond delay for every mock request and equivalent stale cache fixtures.
Match pair numbers and fixture identity.
Include each entry's local refresh work in `time.perf_counter_ns` measurements.
The organization entry also includes its existing scope read.

Report all 40 durations, per-caller medians, actual definition and request counts, and file-write counts.
Report `100 * (before_median - after_median) / before_median`.
Require a result of at least 90% for each caller.
Keep the controlled offline results separate from the issue's reported live 67.3-second observation.
No new elapsed measurement exists during this planning step.

## Phase Outputs and Handoff

### Phase 0: Research

[research.md](research.md) resolves discovery ownership, result propagation, failure handling, cache compatibility, caller wiring, timing, and tool limits.
Research used direct local inspection because this request prohibits another agent.

### Phase 1: Design and contracts

- [data-model.md](data-model.md) defines fields, relationships, invariants, and transitions.
- [contracts/definition-refresh.md](contracts/definition-refresh.md) defines the selected entry and visible compatibility requirements.
- [quickstart.md](quickstart.md) defines the later test, benchmark, and gate commands.

The post-design constitution check appears above.
No shared agent-context file or SpecKit state belongs to this feature's output.
The PowerShell setup command failed because `pwsh` is unavailable.
The agent-context update cannot run on this host and would edit prohibited instructions.
The required companion hook has no installed implementation.
Report its invocation result without claiming that companion state records plan completion.

### Phase 2: Planning handoff

Later implementation must use this order:

1. Add the reserved offline caller tests and record all four red stale-cache results.
2. Record the controlled before measurements through the same four caller entries.
3. Implement selected exporter processing, trustworthy failures, the shared helper, and the client dependency removal.
4. Record green compatibility tests, complete full-export coverage, changed-method coverage, and matching after measurements.
5. Run the configured local gates and prepare only the reserved release-note fragment.

Stop this command after the planning artifacts.
A later local Conventional Commit requires completed validation and the required Copilot App trailer.
This step does not commit.
Do not publish until the parent explicitly releases queue position 17 after [#3335](https://github.com/jmorrison-juniper/MistHelper/issues/3335).

## Requirement Trace

| Requirements | Design authority | Required evidence |
| --- | --- | --- |
| FR-001, FR-002, FR-012 | Validated selected discovery in the exporter. | Four real stale callers, invalid selections, and zero unrelated cache access or change. |
| FR-003 | Existing `_is_file_fresh`. | Fresh, one-second-before, exact-boundary, expired, missing, unreadable timestamp, and second-run cases. |
| FR-004, FR-008 | Shared helper and unchanged caller contracts. | Return values, banners, prompts, filenames, and existing empty outputs. |
| FR-005 | Existing dynamic `export_all` and special dispatch. | All 28 baseline names, fresh skips, and model/country/channel handling. |
| FR-006, FR-007 | Existing normalization and scope reader. | Exact CSV fields, values, interval text, and ordered results for all four scopes. |
| FR-009, FR-010 | First-error return chain and existing counters. | HTTP, transport, discovery, writer, secondary fallback, and repeated-attempt failures. |
| FR-011 | Before-and-after logs in changed blocks. | ASCII, safe error text, status, counts, and no false success. |
| FR-013 | Temporary files and offline seams. | No credentials, live services, stores, containers, or checkout data writes. |

The [quickstart](quickstart.md) also defines evidence for SC-001 through SC-007.
It retains the configured gate thresholds and test-quality ratchet.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| --- | --- | --- |
| A selected entry adds a method to the existing oversized exporter class. | The reserved scope requires that semantic owner to control selected discovery and processing. | A new wrapper or framework violates the scope and duplicates ownership. A class-wide redesign is unrelated. |
| The reserved new test adds a child to the existing oversized export test directory. | It must prove four actual callers through real exporter code before implementation. | A new test package falls outside the user's explicit file reservation. Existing baseline test files cannot be edited. |
| Required planning documents exceed five direct children in the feature directory. | SpecKit requires a plan, research, model, contract, and validation guide beside the existing spec and checklist. | Moving required artifacts changes their expected workflow paths. No executable hierarchy grows from these documents. |

These exceptions do not relax new function limits or authorize unrelated changes.

## Planning Execution Record

This step generated five documents within the feature directory.
It left the existing specification and checklist unchanged.
Structural artifact checks found no unresolved markers, non-ASCII text, trailing whitespace, or missing template sections.

The configured STE linter read all five new documents.
The plan, research, model, and validation guide scored 97.
The contract scored 98.
These are structural results only. The configured dictionary is absent.

The standard Markdown link tool scanned zero tracked files because these feature files are untracked.
That result does not validate their links.
A separate offline check read all seven feature documents and verified 62 local links and anchors.
It retained 16 external links without network requests.

The required setup script and agent-context script attempts each failed with exit code 127 because `pwsh` is absent.
The required `speckit.companion.after-plan` invocation also failed with exit code 127 because its command is not installed.
The optional commit hooks did not run.
No replacement companion state, shared SpecKit state, or agent instructions changed.
Automatic workflow state completion remains unavailable.

No implementation tests, benchmarks, code gates, commits, pushes, or pull request operations ran during this step.

## References

- [Specification](spec.md) and [requirements checklist](checklists/requirements.md).
- [Scope claim](https://github.com/jmorrison-juniper/MistHelper/issues/3300#issuecomment-5936871419).
- [Related issue #3266](https://github.com/jmorrison-juniper/MistHelper/issues/3266).
- [Current CI workflow](../../.github/workflows/ci.yml) and [project configuration](../../pyproject.toml).
- [STE writing guide](../../documentation/ASD-STE100_writing-guide.md).
