# Validation Guide: Deprecated SLE operation removal

**Issue**: [#3335](https://github.com/jmorrison-juniper/MistHelper/issues/3335)

**Design**: [Plan](plan.md), [data model](data-model.md), and [contract](contracts/endpoint-removal.md).

## Authorization and Prerequisites

These commands describe later local implementation validation.
The coding session completed the local tests, generators, and audits in [the task evidence](tasks.md).
The coordinator authorizes the validated local metadata commit.
Publication still requires the explicit position-16 grant.

### Scope limit

Both offered trend entries remain available and resolve to real SDK functions.
This metadata-only change does not repair their documented object-output behavior.
[Issue #3699](https://github.com/jmorrison-juniper/MistHelper/issues/3699) records the separate existing defect.
Its real SDK proof decodes both documented objects at HTTP 200 with no next page.
`get_all` then returns zero rows, while `_normalize` retains the raw object as one row.
Do not interpret passing generic list and `results` fixtures as verified exports of those documented objects.

Use the repository root:

```text
/Users/jmorrison/GitHub/copilot-worktrees/MistHelper/jmorrison-juniper-fictional-barnacle
```

The parent prepared `.venv` with Python 3.13.13, mistapi 0.64.0, runtime and development requirements, and Chromium.
Do not reinstall or rerun bootstrap.
Do not change the `mistapi>=0.64.0,<0.65` pin.
Use this worktree's environment, not another checkout's interpreter or audit lock.
All commands below start from this repository root and use `rtk proxy`.

Use only local HTTP and output boundaries for new trend tests.
No Mist token, live Mist call, persistent database, container, or cloud resource is required.
Existing SQLite regressions use pytest temporary directories.
Never direct them at `data/mist_data.db`.

## 1. Capture Red Evidence Before Removal

First add the exact-name regression cases in the two reserved test modules.
Do not remove registrations before this red run.

Run the new parameterized guard cases:

```bash
rtk proxy .venv/bin/python -m pytest tests/guardrails/test_endpoint_catalog.py::TestCatalogCoverage -k deprecated -q
```

The guard test names must contain `deprecated`.
Require six collected live-source absence cases.
They check two exact retired identifiers against selectable rows, catalog keys, and PK metadata keys.
The identifiers are `getSiteSleSummary` and `getSiteSleClassifierDetails`.
All six must fail because the current registrations contain the named operation.
Each diagnostic must report the actual inspected count.

The starting measurements are 286 selectable rows, 286 catalog entries, and 571 PK keys.
An import error, unreadable input, empty source, zero collected cases, or skip is not red evidence.
Keep the same six assertions for the green run.

## 2. Capture Green and Controlled-Rejection Evidence

After the bounded removal and three label corrections, run:

```bash
rtk proxy .venv/bin/python -m pytest tests/guardrails/test_endpoint_catalog.py tests/unit/export/test_endpoint_family_exporter.py -q
```

Require:

- Site SLE 15, stage two 132, and catalog 284.
- Neighboring family counts 7, 33, 61, 10, and 6, with unchanged members.
- Six direct live-source absence cases passing.
- Six direct injected-source guard decisions rejecting the exact injected identifier.
- Empty, missing, malformed, and unreadable sources rejecting rather than skipping.

Measure the live and copied input sizes inside the guard.
Expected post-removal measurements on this baseline are 284 selectable rows, 284 catalog entries, and 569 PK keys.
One injected registration produces 285, 285, or 570 inspected records.
Partial read failures report the actual successfully read count.
No empty or unreadable input may produce a passing decision.

Do not edit the quality baseline to make these tests pass.
Do not add logs or comments for obvious test actions.

## 3. Exercise Both Real SDK Invocations

The exporter module must include real SDK trend cases, with `trend` in their test names.
Run those cases:

```bash
rtk proxy .venv/bin/python -m pytest tests/unit/export/test_endpoint_family_exporter.py -k trend -q
```

Require nonzero collection for both exact trend identifiers.
They are `getSiteSleSummaryTrend` and `getSiteSleClassifierSummaryTrend`.
Follow [contract C3 through C5](contracts/endpoint-removal.md#c3-retained-sdk-resolution-and-requests).

Use a real SDK session on a `.test` host and an empty local environment file.
Create fresh `data/SiteList.csv` input under the test's temporary directory.
Supply an existing `AppContext` with the local session and organization.
Mock only that session's HTTP `get` transport, console input, and final writer.
Return real `requests.Response` objects for the site lookup and trend responses.
Set each response's status, JSON body, URL, and prepared request headers.
Use real SDK response decoding and pagination.
Require no SDK error log on a successful journey.

Check both list payloads and dictionary payloads containing `results`.
Include a local next-page case.
Assert literal normalized, flattened, and escaped records, the exact filename, and the original routing identifier.
Check the default empty query and optional query construction through the real SDK.
Run repeated payloads and compare exact dispatch arguments.
Do not infer a new natural key or deduplication contract.

Repeat both full journeys with both deprecated attributes absent from the actual SDK module.
Restore those attributes after each case.
Do not replace SDK operation methods, `_resolve`, required-answer collection, `get_all`, or normalization.
These fixtures preserve existing generic processing.
The separate issue owns canonical object-response coverage and any response repair.

Run empty-result and required-answer cancellation cases.
Blank input, EOF, interruption, and invalid site selection must not make a trend request or final writer call.
The existing empty behavior for an SDK dictionary without `results` also remains unchanged.

## 4. Run Existing Regressions Without Edits

Run the complete portal label and required-answer modules:

```bash
rtk proxy .venv/bin/python -m pytest tests/unit/web_portal/test_portal_label_accuracy.py tests/unit/web_portal/test_portal_required_answers.py -q
```

The portal and command-line labels must both promise the actual 15 SLE options.
All existing chooser orders, dynamic required controls, browser-runnable flags, and label read floors remain unchanged.
Do not reduce a floor or rewrite either module.

Run the existing export contract and focused key and dispatch selectors:

```bash
rtk proxy .venv/bin/python -m pytest \
  tests/contract/test_export_api_function_names.py::test_source_export_calls_name_the_api_function \
  tests/unit/db/test_database_schema_utils.py::TestGetEndpointStrategy \
  tests/unit/db/test_database_schema_utils.py::TestBuildNaturalPkSql \
  tests/unit/db/test_database_schema_utils.py::TestBuildCompositePkSql \
  tests/unit/db/test_database_schema_utils.py::TestBuildAutoincrementSql \
  tests/unit/db/test_database_schema_utils.py::TestBuildCreateTableSql \
  tests/unit/export/test_data_exporter.py::TestWriteWithFormatSelection \
  tests/unit/export/test_data_exporter.py::TestRouteToPolyglot -q
```

Run the existing temporary SQLite upsert classes:

```bash
rtk proxy .venv/bin/python -m pytest \
  tests/integration/test_menu_12_sqlite_upsert.py::TestSQLiteUpsertIdempotency \
  tests/integration/test_menu_13_sqlite_upsert.py::TestSQLiteUpsertIdempotency -q
```

These selectors prove existing inventory and device-statistics key and update behavior.
They do not authorize a new trend strategy or a live database write.

Run the parent-completed SLE refusal regression:

```bash
rtk proxy .venv/bin/python -m pytest tests/unit/export/test_export_notice_separator.py::test_a_refused_insight_request_names_the_http_status -q
```

The refusal cases must retain the HTTP status, preserve previous output, and make no writer call.
No false empty-result notice, success notice, or secret value may appear.
Do not edit the test or its production owner.

## 5. Renew the Live Conflict Check Before Generation

Authenticate with `gh api user` and read issue #3335 and its exact reservation comment.
Read all currently open PRs, then every paginated exact PR file list.
Do not use only PR titles, diff statistics, directory ownership, or a first page.
Compare file-list size with each PR's `changed_files`.
Include previous filenames for renames.
Confirm that the PR set and heads remain stable through the check.

The planning check found 12 complete PR lists, 103 exact file entries, and no overlap.
That result does not replace this later check.
Stop on overlap or incomplete or changing evidence.
Do not expand the 23-path reservation.

## 6. Generate Only the Six Reserved Reference Files

Run only after the renewed check:

```bash
rtk proxy .venv/bin/python scripts/generate_menu_wiki.py
rtk proxy .venv/bin/python -m scripts.menu_api_map
```

Run the same two commands a second time.
Compare the six outputs' bytes before and after that second run.
Keep comparison snapshots in memory, not in another tracked artifact.
All six byte comparisons must match.

The outputs are listed in [contract C7](contracts/endpoint-removal.md#c7-references-and-regression-boundary).
The wiki copies must also match each other.
Check active operation maps for each exact retired identifier, not its prefix.
Both trend identifiers must remain.
Every menu 263 label must state 15.

Then run the non-writing map gate:

```bash
rtk proxy .venv/bin/python -m scripts.menu_api_map --check
```

Do not pass `--refresh-sdk-index`.
Do not change `scripts/menu_api_map/reference/sdk_index.json` or upstream API references.
If another generated path changes, stop and report it.
Do not include it or automatically restore another worker's edits.

## 7. Run Full Configured Code Gates

Use the installed tools with unchanged settings:

```bash
rtk proxy .venv/bin/ruff check .
rtk proxy .venv/bin/black --check --diff .
rtk proxy .venv/bin/python -m py_compile MistHelper.py
rtk proxy .venv/bin/mypy src/ MistHelper.py wsgi.py scripts/mist_ideas_analyzer_pkg/__init__.py scripts/mist_ideas_distiller_v2_pkg/__init__.py --config-file pyproject.toml
rtk proxy .venv/bin/bandit-exclude-check --include-sample ./src/utils/zen_city_metadata.py --include-sample '.\src\utils\zen_city_metadata.py'
rtk proxy .venv/bin/bandit -c pyproject.toml -r .
```

The mypy targets are the exact current CI `MYPY_PATHS`:

```text
src/ MistHelper.py wsgi.py scripts/mist_ideas_analyzer_pkg/__init__.py scripts/mist_ideas_distiller_v2_pkg/__init__.py
```

Do not narrow Ruff or Black to changed files.
Do not add a Bandit severity filter, skip rule, or exclusion.

Run the unchanged test-quality ratchet:

```bash
rtk proxy .venv/bin/test-quality-analyzer --gate --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json
```

Use its existing full local scope while the changes are uncommitted.
The CI changed-file mode compares revisions, so it is not proof for uncommitted test edits.
Do not write or prune the baseline, disable a rule, or broaden old test rewrites.
Retain the result and measured gate scope as local evidence only.

## 8. Check Documentation Links and STE

Run the existing repository Markdown link gate:

```bash
rtk proxy .venv/bin/markdown-link-check --exclude 'documentation/wiki/**'
rtk proxy .venv/bin/python -m pytest tests/guardrails/test_markdown_links.py -q
```

The checker lists tracked Markdown files only.
Before tracking is authorized, directly read all five new design files with the existing checker's file parser.
Require five readable files and validate every local link and anchor.
A successful command that inspected zero new design files is not evidence for them.
Do not stage files merely to make the checker see them during planning.

Run STE with the unchanged configuration and current minimum of 80:

```bash
rtk proxy .venv/bin/ste-linter --config .ste-linter.toml --min-score 80 \
  specs/3335-deprecated-sle-operations/plan.md \
  specs/3335-deprecated-sle-operations/research.md \
  specs/3335-deprecated-sle-operations/data-model.md \
  specs/3335-deprecated-sle-operations/quickstart.md \
  specs/3335-deprecated-sle-operations/contracts/endpoint-removal.md \
  documentation/menu-highlights.md \
  documentation/menu_reference.md \
  documentation/wiki/Menu-Reference.md \
  documentation/menu-api/README.md \
  documentation/menu-api/interactive-safe.md \
  documentation/wiki/Menu-API-Endpoints.md \
  documentation/wiki/Menu-API-Endpoints-Interactive-Safe.md \
  changelog.d/issue-3335-deprecated-sle-operations.md
```

Do not lower the minimum or add an allowlist entry.
If the optional word dictionary is unavailable, report the tool's partial coverage explicitly.
Do not generate or change shared dictionary data during isolated planning.
The release fragment must describe both exact removals and both retained trend operations.
Keep the shared README, changelog, instructions, and operator guide unchanged.

## 9. Audit Runtime Dependencies Without Ignored Advisories

Try the standard runtime audit:

```bash
rtk proxy .venv/bin/python -m pip_audit -r requirements.txt
```

If the standard macOS pip resolver fails, retain the failure output.
The authorized strict alternative is this worktree's own hashed runtime lock.
During later validation only, create the `data/issue-3335/` directory for that local audit file if it is absent.
Then run:

```bash
rtk proxy env UV_NATIVE_TLS=1 UV_SYSTEM_CERTS=1 uv pip compile requirements.txt --python .venv/bin/python --generate-hashes --output-file data/issue-3335/runtime-audit-lock.txt
rtk proxy .venv/bin/python -m pip_audit --no-deps --disable-pip --require-hashes -r data/issue-3335/runtime-audit-lock.txt
```

The compile command resolves requirements but does not install them.
Do not reuse another worktree's lock.
Do not change a manifest, remove a requirement, or use `--ignore-vuln`.
Require a complete audit with zero advisories.

The Git-only `misthelper-devtools` development pin is separate:

```text
git+https://github.com/jmorrison-juniper/misthelper-devtools.git@b140350ebc40e61b57a3a65731c0df520f143661
```

It belongs to `requirements-dev.txt`, not the runtime lock.
State that exclusion by dependency scope.
Do not claim the runtime audit covers Git-only development tooling.

## 10. Review the Bounded Diff and Stop

Read status and whitespace evidence:

```bash
rtk proxy git --no-pager diff --check
rtk proxy git --no-pager diff --stat
rtk proxy git status --short
```

Require only reserved feature changes.
Verify that the three source diffs delete only the two exact registrations.
Verify unchanged retained row fields, neighboring memberships, PK dictionaries, merge behavior, top-level menu identity, categories, and safety flags.
Record red and green results, six injected rejections, actual scan counts, SDK absence results, gate exits, and generator byte equality.

Complete the authorized local preparation and commit.
Stage only the reserved files after all local evidence and the analysis disposition are recorded.
Use Conventional Commits and the Copilot trailer from [plan.md](plan.md).
Do not fetch, rebase, push, open a PR, merge, deploy, or mutate stores or containers now.
The parent owns publication at position 16 after issue #3366.
Wait for the parent's separate publication release.
