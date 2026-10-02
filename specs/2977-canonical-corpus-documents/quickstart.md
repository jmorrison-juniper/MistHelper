# Validation Guide: Canonical Corpus Documents

## Status and prerequisites

This guide describes later implementation validation.
The file-only planning stage did not run these acceptance tests or audits.
Run the commands only when that implementation stage is authorized.
Use [contracts/storage.md](contracts/storage.md) for expected behavior.
Use [data-model.md](data-model.md) for schema and migration assertions.

- Use the existing worktree's Python 3.13.13 `.venv`, restored with `uv` from unchanged requirements.
- Keep `requirements.txt`, `requirements-dev.txt`, SDK pins, and all gate configuration unchanged.
- Use original synthetic payloads, a local fake client, and temporary local corpus roots.
- Use no live document downloads, historical Windows files, copied PDF fixtures, or external uploads.
- Keep payloads at most 8 KiB for the stress proof.
- Keep proof reports outside committed feature files.
- Run each gate separately. Stop when a required gate fails.

Run commands from the repository root in one shell.
Reactivate the same environment for each new tool process when needed.
On Windows, use the equivalent `.venv` interpreter and native path syntax.

```bash
set -o pipefail
source .venv/bin/activate
export PYTHONDONTWRITEBYTECODE=1
export PYTHON="$PWD/.venv/bin/python"
export VALIDATION_DIR="$(mktemp -d)"
rtk proxy "$PYTHON" --version
```

Use the authorized temporary directory for coverage and hashed audit output.
These commands do not authorize new dependencies or changes to checked-in manifests.

The initial local baseline was 183 passes and three historical-manifest skips.
Those skips require the absent `data/juniper_corpus_smoke/manifest.json`.
All committed parser fixtures exist.
Keep the historical tests and parser fixtures unchanged.
Do not fabricate historical evidence.
Every new prevention case must run without a skip.

## 1. Record the real-flow red regression

Add the regression in the reserved `test_download_flow.py`.
Use `TestCanonicalDownloadFlow.test_equal_bytes_across_names_and_categories` as its stable test node.
Run it against the unfixed production download flow before implementation.

```bash
rtk proxy "$PYTHON" -B -m pytest -p no:cacheprovider -s -q \
  tests/unit/juniper_docs/canonical/test_download_flow.py::TestCanonicalDownloadFlow::test_equal_bytes_across_names_and_categories
```

The test uses two distinct resolved URLs, two names, and two categories.
Both responses contain identical original synthetic bytes.
Use the actual downloader, allocator, temporary state, and file publication.
Do not mock the download result or content-allocation decision.

Expected red evidence:

- The fake client records two fetches.
- The assertion expects one complete physical PDF and one payload write.
- The existing flow produces duplicate files, bytes, or writes, so the assertion fails.
- Preserve the observed counts and failure, not an expected-failure marker.

## 2. Require the same test to become green

After implementation, rerun the same test node.
Then run the complete reserved canonical unit suite and manifest contract.

```bash
rtk proxy "$PYTHON" -B -m pytest -p no:cacheprovider -s -q \
  tests/unit/juniper_docs/canonical \
  tests/contract/juniper_docs/test_canonical_manifest.py \
  --timeout=120
```

Expected equal-content results:

| Observation | Required value |
| --- | --- |
| Actual client fetches | 2 |
| Result statuses | First `downloaded`, second `skipped` |
| Complete physical PDFs | 1 |
| Complete payload writes | 1 |
| Physical bytes | The independently calculated size of the one payload |
| Natural URL rows | 2 |
| Canonical paths | The same valid file |
| Content digests | The same independently calculated full SHA256 |

Assert observed files and byte totals.
Do not derive an expected value from the result under test.
Exclude `.part` files from complete payload counts.
Do not claim a bandwidth saving when both URLs were fetched.

## 3. Prove inventory, restart, and response boundaries

In `test_canonical_manifest.py`, render the actual JSON and CSV manifests.
Compare every existing field with independently prepared source records.
Check original names, additive digests, resolved URLs, candidates, scores where exposed, stages, and labels.
Check null-to-empty CSV behavior for the two additive fields.
Check that `total_bytes` counts the canonical path once.
URL and category totals must still count both rows.

Close the actual store.
Create new store, allocator, and downloader instances.
Request every persisted alias with a fake client that fails on any fetch.
Assert zero fetches, payload writes, and stored-file digest bytes.
Render both manifests again and check every alias.

Required response cases:

- Different names and categories with equal bytes use one file.
- Equal bytes reuse a canonical file outside the requesting category.
- Different bytes with the same basename retain both complete files.
- A saved valid same URL resumes without a fetch.
- Several root URLs for one resolved URL keep their independent histories.
- A fetched changed response updates roots for that resolved URL.
- Different-URL aliases of its old digest retain their old content identity.
- Verified recovery of the expected digest repairs every corresponding alias pointer.
- Separate corpus roots do not share files or trusted cache entries.

## 4. Prove invalid-file and interruption behavior

Use `test_content_index.py`, `test_download_flow.py`, and `test_state_migration.py`.
Inject faults at the actual boundary.
Do not skip a case because an administrator account can read a restricted file.

| Boundary | Required cases | Expected result |
| --- | --- | --- |
| Canonical file | Missing, empty, lost prefix, and digest mismatch | No skip. Verified recovery or explicit failure. |
| Identity | Same-size changed bytes with restored mtime, replaced inode/device, and changed ctime | Revalidation detects the change. |
| Hash read | Permission error, read error, and identity changes during reading | Explicit failure with no trusted receipt. |
| Stat/open | Path or descriptor stat failure, unreadable file, and unreliable required identity | Explicit failure, not weakened validation. |
| Publication | Interrupted `.part`, write failure, and replacement failure | No completed association to incomplete content. |
| Post-publication | Stop after replacement but before required state completion | No successful counter. Later verified adoption avoids another equal write. |
| Persistence | Locked, damaged, unwritable, failed transaction, and failed read-back | Fatal store failure. Writes are never silently disabled. |
| Runner resume | Invalid file under downloaded or classified stage | Final stage does not bypass validation. |

Inspect return status, failure reason, state, cache, counters, and complete files.
After repair, reopen the store and verify every affected alias.
No required case may skip.

## 5. Prove migration and legacy adoption

Prepare an original synthetic version 1 database through the existing state contract.
Populate every legacy table with distinct values.
Include nullable paths, final stages, candidates, scores, drop reasons, categories, flags, and timestamps.
Keep committed records in WAL when testing backup recovery.

Verify all of the following:

- The backup uses the SQLite backup API and includes committed WAL records.
- The verified backup remains version 1 and retains complete row values.
- Migration preserves all existing columns, keys, rows, candidate choices, scores, and metadata.
- New document fields start null and the cache starts empty.
- The version changes to 2 only with the atomic verified upgrade.
- Repeated opening neither repeats migration nor creates duplicate rows.
- Explicit indexing adoption populates digests from valid local files without fetching.
- Legacy original names come from authoritative metadata, not collision-renamed paths.
- Missing cache rows require validation before trusted reuse.
- Migration failures roll back or retain a verified recoverable prior state.
- Failed committed verification does not open the store for normal use.
- Unknown, malformed, newer, and incompatible schemas fail without accepted changes.
- Unsupported downgrade does not edit the version.
- Backup restoration is tested only with explicit recovery authority and quiescent writers.
- Migration and adoption do not delete pre-existing duplicate files.

Compare all legacy row values, not only counts.
Do not alter scores, stage meanings, or candidate reasons to make the test pass.

## 6. Prove all three path consumers

Use `test_path_consumers.py`.
Prepare multiple natural URL rows for one physical payload with distinct labels.
Exercise `HarvestRunner`, `CorpusReclassifier`, and `ManualDocumentSorter` separately.

For each consumer:

1. Check first-payload placement before later aliases attach.
2. Attach later aliases without another file or a category-only move.
3. Check a shared-path label update without relocation.
4. Perform an authorized real move and verify every alias path and cache key.
5. Restart and validate every alias and both manifests.

Also check equal source/destination, different-byte destination collisions, stale input rows, and interrupted state updates.
Manual sorting must process one physical payload once and retain the entire alias group.
Repeat the pass and require idempotent results.

Snapshot files, database values, and durable cache before default dry runs.
Require no moves, backups, migrations, adoption, pointer changes, or cache writes.
Check every alias after the dry run.

## 7. Measure bounded work independently

The stress test uses 1,000 distinct URLs and 20 distinct payloads.
Each payload is original and no larger than 8 KiB.
Use the real download flow and a shared allocator.
Observe production boundaries without replacing their results.

Record these counters separately:

- Document fetches and fetched-payload digest calls/bytes.
- Stored-file digest calls/bytes and maximum read request size.
- URL-name hash work, separate from content digest work.
- Corpus discovery walks.
- Complete payload writes and replacements.
- Complete physical PDF count and physical bytes.
- Natural URL row count and alias paths.

Required first-run evidence:

- One discovery walk.
- 1,000 fetches and at most one fetched-payload digest pass per response.
- Twenty complete payload writes and twenty complete physical PDFs.
- Physical bytes equal the independently calculated sum of the twenty unique payload sizes.
- No repeated stored hashing caused by unchanged aliases.

Required unchanged-restart evidence:

- All 1,000 aliases remain valid.
- One discovery walk, with no new walk per request.
- Zero document fetches, payload writes, and stored-file digest bytes.

Use a separate cold-cache scenario with pre-existing synthetic PDFs.
Measure `S`, `U`, and `C` from independently expected files and identity changes.
Require stored-file digest bytes no greater than `S + U + C`.
Require maximum stored-file reads no greater than 1,048,576 bytes.
Do not claim measurements from the absent historical corpus.

## 8. Run harvest regressions and changed-method coverage

Run the complete relevant harvest suite without required skips.
Do not select only the new tests.

```bash
rtk proxy "$PYTHON" -B -m pytest -p no:cacheprovider \
  tests/unit/juniper_docs \
  tests/contract/juniper_docs/test_canonical_manifest.py \
  --timeout=120 --cov=src/juniper_docs --cov-branch \
  --cov-report=term-missing \
  --cov-report=json:"$VALIDATION_DIR/canonical-coverage.json" \
  --cov-fail-under=80
```

Report each changed production method with its qualified name, executable lines, covered lines, and percentage.
Require at least 80 percent executable-line coverage for every changed method.
An aggregate package result cannot replace that report.
Retain the configured CI coverage gate separately.
Do not add exclusions, suppressions, baseline changes, or expected-failure substitutes.
The absent historical manifest blocks historical acceptance only.
Every new prevention case must run without a skip.

## 9. Run the configured code and quality gates

Use the scopes from [.github/workflows/ci.yml](../../.github/workflows/ci.yml).
The following commands retain its full Ruff, Black, mypy, Bandit, and complexity scopes.

```bash
rtk proxy "$PYTHON" -m ruff check .
```

```bash
rtk proxy "$PYTHON" -m black --check --diff .
```

The next command uses the exact configured `MYPY_PATHS`.

```bash
rtk proxy "$PYTHON" -m mypy \
  src/ MistHelper.py wsgi.py \
  scripts/mist_ideas_analyzer_pkg/__init__.py \
  scripts/mist_ideas_distiller_v2_pkg/__init__.py \
  --config-file pyproject.toml
```

```bash
rtk proxy bandit-exclude-check \
  --include-sample ./src/utils/zen_city_metadata.py \
  --include-sample '.\src\utils\zen_city_metadata.py'
```

```bash
rtk proxy "$PYTHON" -m bandit -c pyproject.toml -r .
```

The complexity scope also matches the configured `RADON_PATHS`.

```bash
rtk proxy radon cc \
  src/ MistHelper.py wsgi.py \
  scripts/analyze_marvis_pcap.py scripts/probe_zscaler_endpoints.py \
  tests/unit/utils/test_zscaler_catalogue.py -a -nb
```

```bash
rtk proxy radon cc \
  src/ MistHelper.py wsgi.py \
  scripts/analyze_marvis_pcap.py scripts/probe_zscaler_endpoints.py \
  tests/unit/utils/test_zscaler_catalogue.py -j | rtk proxy complexity-gate --max 10
```

Run required-input preflight before each test-quality analyzer invocation.
Keep all six required inputs readable and all three active guide procedures valid.
Zero analyzer findings do not prove readable required inputs.

```bash
rtk proxy "$PYTHON" -B -m pytest -p no:cacheprovider -s -q \
  tests/guardrails/local_test_quality_loop/test_guidance.py::TestLiveGuides
```

Before the local commit, run the unchanged complete ratchet against the working content.

```bash
rtk proxy test-quality-analyzer --gate \
  --config .github/test-quality-config.toml \
  --baseline .github/test-quality-baseline.json
```

After a separately authorized local commit, require clean exact relevant scope.
Repeat preflight, then check the committed two-endpoint difference against the known local base.
The reported initial base is `b7ce8eecea305c20b498e12b3f3446ae662663ea`.
Verify that it exists locally before using it.
Do not fetch or substitute another base under the file-only grant.

```bash
rtk proxy test-quality-analyzer --gate \
  --config .github/test-quality-config.toml \
  --baseline .github/test-quality-baseline.json \
  --changed-from b7ce8eecea305c20b498e12b3f3446ae662663ea \
  --full-gate-path .github/workflows/ci.yml \
  --full-gate-path requirements-dev.txt
```

This offline base check is not acceptance against a later granted main revision.
The analyzer compares the base and `HEAD`, then reads selected working files.
Dirty or uncommitted tests cannot satisfy its committed-scope proof.
Require zero new findings and record scope, parsed inputs, and exit status.

Run any other configured gate applicable to the reserved paths.
Use [documentation/quality-gates.md](../../documentation/quality-gates.md) and the workflow as the authority.
Do not narrow a gate to this package or alter an exclusion to hide a failure.

## 10. Check links and configured STE

Use explicit artifact paths and confirm that every file was checked.
A zero exit with zero selected files is not evidence.
The packaged link checker only selects tracked files.
If new artifacts are untracked, validate their local targets directly without staging them.
Repeat the configured check after a separately authorized local commit.

```bash
rtk proxy markdown-link-check --root "$PWD" \
  specs/2977-canonical-corpus-documents/plan.md \
  specs/2977-canonical-corpus-documents/research.md \
  specs/2977-canonical-corpus-documents/data-model.md \
  specs/2977-canonical-corpus-documents/quickstart.md \
  specs/2977-canonical-corpus-documents/contracts/storage.md \
  documentation/free-juniper-corpus.md \
  changelog.d/issue-2977-canonical-corpus-documents.md
```

```bash
rtk proxy ste-linter --config .ste-linter.toml --min-score 80 --format json \
  specs/2977-canonical-corpus-documents/plan.md \
  specs/2977-canonical-corpus-documents/research.md \
  specs/2977-canonical-corpus-documents/data-model.md \
  specs/2977-canonical-corpus-documents/quickstart.md \
  specs/2977-canonical-corpus-documents/contracts/storage.md \
  documentation/free-juniper-corpus.md \
  changelog.d/issue-2977-canonical-corpus-documents.md
```

Record the score, exit status, checked paths, and dictionary availability.
If the configured dictionary is absent, record `dictionary_unavailable`.
Do not call that result a dictionary-backed STE pass.
Do not edit the dictionary path, configuration, allowlist, or rule selection.

## 11. Audit unchanged runtime dependencies in two modes

First use the standard resolver with strict dependency collection.
Do not use no-dependency mode for this first proof.

```bash
rtk proxy "$PYTHON" -m pip_audit \
  -r requirements.txt --strict --progress-spinner off
```

Then compile the complete runtime dependency set with hashes.
Use the same interpreter, platform, unchanged input, and index policy.

```bash
rtk proxy uv pip compile requirements.txt \
  --python "$PYTHON" --generate-hashes \
  --output-file "$VALIDATION_DIR/runtime-hashed.txt"
```

Verify that every resolved runtime requirement is pinned and has complete distribution hashes.
Do not omit transitive dependencies or direct requirements.
The compilation must not change the repository requirements.

```bash
rtk proxy "$PYTHON" -m pip_audit \
  -r "$VALIDATION_DIR/runtime-hashed.txt" \
  --strict --require-hashes --no-deps --disable-pip --progress-spinner off
```

Record a standard-resolver failure as blocked, not zero findings.
If `ensurepip` aborts, use the complete hashed UV resolution for the strict runtime audit.
Require successful hashed collection and zero unaddressed vulnerabilities.
State that this substitute does not prove a standard-resolver pass.
A proxy, service, or network failure in the hashed audit still blocks acceptance.
Do not use `--fix`, ignored vulnerabilities, TLS bypasses, or dependency changes.

`requirements-dev.txt` includes Git-only `misthelper-devtools` at the pinned commit.
Its pin is `b140350ebc40e61b57a3a65731c0df520f143661`.
The hashed runtime audit does not cover that Git source.
Version-only advisory lookup cannot prove the safety of that exact Git tree.
Report this limitation explicitly.
Do not remove the Git requirement or claim a complete development-tool audit.

## 12. Record acceptance and stop at the grant boundary

Record red and green results, complete regression results, required skips, and per-method coverage.
Record all failure scenarios, migration/backup evidence, alias restarts, manifest comparisons, and path consumers.
Record independent stress counters and all configured gate results.
Keep evidence free of document body text and secrets.

A later authorized local commit must be one Conventional Commit with the exact requested `Co-authored-by` trailer.
Confirm the trailer from the parent if it is unavailable.
Do not invent an author or email.
Require clean exact scope after the checks and commit.
The local receipt does not replace protected release acceptance.

The protected position is 30, after issue 3575.
No remote grant currently exists.
Stop before push or pull request until the parent supplies a full verified main SHA.
Exact actual-main tests, protected merge, main image revision checks, and deployment are later conditional work.
Repeat affected evidence when the base, candidate, or checked content changes.
Do not report those steps, issue closure, historical cleanup, or historical measurements as completed.
