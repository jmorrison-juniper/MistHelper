# Validation guide for issue #3436

## Environment

Use only this worktree's Python 3.13 environment.
Do not read another checkout, copy credentials, or copy a licensed dictionary.

The initial `.venv/bin/python --version` failed because the environment did not exist.
The unchanged `python3.13 scripts/bootstrap_worktree.py` then failed in `ensurepip` with `SIGABRT`.
The SpecKit PowerShell branch hook failed because `pwsh` is unavailable.
These failures do not count as successful checks.

The isolated recovery used these commands through RTK.

```bash
rtk proxy uv venv --clear --seed --python python3.13 --link-mode copy --system-certs .venv
rtk proxy uv pip install --python .venv/bin/python --system-certs --link-mode copy -r requirements.txt -r requirements-dev.txt
```

The recovery changes only the ignored own environment.
The source bootstrap and dependency manifests stay unchanged.

## Native acceptance cases

Use `tests/support/sdk_pages.py` without an edit.
Build real transport answers with `Content-Type` and `X-Page` headers.
Let the SDK construct each native next link.
Patch only the initial SDK endpoint and the session's later transport boundary.

Cover later `403`, `404`, `429`, `500`, and `503`.
Cover HTML, a JSON error map, malformed JSON, unreadable body, absent status, and raised transport failures.
Cover a failure after two valid pages.
Cover malformed individual records, complete pages, first-page faults, and zero rows.
Cover a valid collapsed virtual chassis whose header count differs from its row count.

Assert exact endpoint parameters, next links, call counts, rows, and reason dictionaries.
Assert zero live `requests.Session.request` calls.
Assert zero store and firmware write callbacks.
Build the actual final capture for wireless and tier 3 cases.

## Red and negative proofs

Before production edits, run the new acceptance cases on starting main:
`5d38898af5639e90715ec57eb8d48d2985e1acf8`.
Count the failing cases and identify all five surfaces.
After the repair, run the same cases green.
Also remove the checked walk narrowly in memory and prove that the acceptance decision fails.
Print the measured case count.
Do not publish a bad commit.

## Local gates

Run the focused new packages and the complete relevant capture and gate selections.
Run the applicable portal contract and offline integration tests.
Record skips by their exact missing capability.
A skip is not a pass.

Use the repository's configured compile, Ruff, Black, mypy, Bandit, complexity, and documentation commands.
Read each CI scope from `.github/workflows/ci.yml`.
Measure changed statements and branches from coverage data.
Do not hide an uncovered result surface with an exclusion.

Run the live-guide input preflight before test-quality analysis.
After the local commit, require clean relevant files and use the exact fetched intended base.
Use `--include-mist-api` for any test module that the normal SDK predicate excludes.
Record the discovered, parsed, and analyzed scopes separately.

If the ordinary dependency audit aborts in temporary `ensurepip`, record the failed attempt.
Audit the complete hashed runtime closure with strict hashes and no dependency resolution.
Do not use advisory ignores.
Name any Git-installed development package limitation.

If the STE dictionary is unavailable, preserve the named `dictionary_unavailable` limitation.
Do not claim full dictionary validation.

## Local delivery

Preserve all 23 checklist items of `.github/PULL_REQUEST_TEMPLATE.md` in the offline draft.
Record exact commands and results.
State the checks and remote steps that remain unauthorized.
Commit the necessary owned files once with the required coauthor.
Do not amend.

The parent must grant the actual full verified-main SHA before publication.
Position 39 follows issue #3295.
Issue #3353 remains the current publication owner.
Human review is mandatory for this firmware-evidence repair.

## Verified local evidence

The unchanged-source red run checked 159 cases.
It reported 129 failures and 30 successful controls across all five surfaces.
The final native run passed 217 cases.
The removed-walk mutation failed its acceptance decision as required.
Every native case counted zero live HTTP, store, and firmware callbacks.

The complete relevant selections passed 6,208 tests.
One existing Windows-only real import test skipped on macOS.
That skip is not a pass.
The five changed modules reached 96.83 percent combined coverage with branch measurement.
All 142 operational statements and 30 branch transitions of the changed reader regions have coverage.
No operational result surface has an exclusion.
The type-only import and two overload stubs are not runtime reader regions.

The exact SDK guard checked 546 signatures with zero known failures.
It reported 10 unresolved sites and 366 unverifiable signatures.
The real endpoint tests provide the direct proof for this repair's calls.

The source review checked 255 protected declarations and 11 exact SDK endpoint calls across five modules.
The protected functions, classes, numeric bytes, normalization, and endpoint parameters remain unchanged.
Twelve required read-only boundaries match the starting main SHA.

The normal test-quality scope discovered 11 files and analyzed seven.
Its SDK predicate excluded four files.
The explicit SDK scope analyzed all 11 files.
Both final scopes reported zero findings and zero new findings.
The preflight read all six required inputs and checked all three guides.

The standard dependency audit failed in temporary `ensurepip` with `SIGABRT`.
The authorized strict hashed runtime audit checked 105 packages with zero advisories and zero skipped packages.
The Git-installed development package is outside that runtime closure.
No dependency manifest or advisory ignore changed.

The writing gate checked 26 owned files at threshold 80.
Its minimum score was 89.
Its scope remains `partial` with `dictionary_unavailable`.
The positive Markdown scan checked all nine staged feature documents.
It found zero broken links.

The session evidence holds the offline PR draft.
It preserves all 23 template items and records exact commands, results, and unperformed actions.
The final commit SHA, clean committed-scope results, and handoff follow after the local commit.

## Result responsibility and complete gate proof

The initial local commit remains in history.
Its result class carried an SDK operation.
The pinned analyzer then inferred HTTP risk when three existing tests imported that result class.
Those three new findings were candidate-induced, not pre-existing.

The corrected `DeviceRead` is a passive result with three data fields and no declared operation.
The existing `read_every_page` owns the checked SDK call, response validation, and lost-page reason.
No compatibility alias or wrapper remains.
No outside test, applicability rule, scope, baseline, threshold, or suppression changed.

The exact full default gates on two own immutable main exports each passed.
Each gate discovered 1,001 files, analyzed 953, and checked 725 findings.
Both gates reported zero new findings.
The exports held 6,736 and 6,740 files.
Every file hash remained unchanged during the runs.

The corrected full default gate discovered 1,006 files and analyzed 957.
It checked the same 725 complete finding identities and reported zero new findings.
Only the three candidate-induced obligations disappeared.
Every previous analyzed test and genuine finding remained.
The rehearsal SDK import stays local to its spy fixture, so the normal analyzer still reads that existing test file.

A direct test checks the passive result declaration.
The removed-walk test still rejects the lost-page acceptance decision.
The native and full rehearsal selection passed 235 cases with no live transport or write callback.
The passive result change therefore does not remove a real page-reader guard.
