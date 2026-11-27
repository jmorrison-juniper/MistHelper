# Research: Locked Worktree Bootstrap

**Scope**: Issue #4591. Read-only evidence from the local repository, the GitHub `main` branch, the CI logs, and the upstream uv source. No uv command ran, and no build, test, or install ran.

**Remote head**: `main` is `f03c6c9b36d612a48d7b9652998c2fd87dd777ca`, and the local `HEAD` matches it. The local working tree holds five modified files that do not affect this issue (see `analysis.md`, UNR-07). The evidence uses committed blobs.

## 1. Static Reproduction

### 1.1 Reporter log mapped to the code

The reporter log is from the bootstrap at commit `c57c9b704` (PR #4505, merged 2026-11-05 16:45 UTC). The main head at issue creation was `5d444bda2`. Both commits hold the same bootstrap blob (`dd03b30a694697bee0a7ed9be271cd1b4b4b2f86`) and the same `uv.lock` blob (`4a1674057b1b139ee95265130c38c88772c49d3b`). See RC-31 to RC-34.

| Reporter log line | Reporter-era location (`c57c9b704`) | Current location (`main`, blob `e16515ff`) |
|---|---|---|
| `Synchronizing project dependencies from uv.lock.` | Line 282 (info before the sync) | Line 467 |
| `warning: The UV_NATIVE_TLS environment variable is deprecated and will be removed in a future release. Use UV_SYSTEM_CERTS instead.` | Line 237 sets `UV_NATIVE_TLS`. The uv text is at `crates/uv-cli/src/settings.rs:345` (RC-37). | Line 417 (RC-02) |
| `Resolved 197 packages in 10.03s` | uv output. The lock blob `4a167405` holds 197 package blocks (RC-31). | Same lock count at `5d444bda2` (RC-34) |
| `error: The lockfile at uv.lock needs to be updated, but --locked was provided.` | uv output. The reporter-era script has no stale phrase constant. | Stale phrase at line 153 (RC-08) |
| `The locked UV sync took 11.1 seconds.` | Line 298 (`%s took %.1f seconds.`), with the context from line 284 | Line 533, with the context from line 470 |
| `The locked UV sync failed with code 1.` | Line 302 (`%s failed with code %s.`) and line 303 (exception text) | Lines 537 and 539 |
| `The bootstrap failed: The locked UV sync failed with code 1.` | Line 653 (`The bootstrap failed: %s`) | Line 900 |
| No cause line in the log | No `diagnose_sync_failure` exists at `c57c9b704`. The cause logic landed in PR #4880 (RC-35). | Lines 477 to 493 (RC-05) |
| Index mapping (not in the log) | Lines 230, 231, and 252 (`_effective_sources`) | Lines 432 to 446 (RC-04) |

Conclusion: the reporter log matches the reporter-era code line by line. The log lacks any cause line because that code had no diagnosis.

### 1.2 Lock and pyproject comparison

| Check | Result | Source |
|---|---|---|
| Lock header at the reporter commit | `revision = 3`, `requires-python = ">=3.13"`, 197 package blocks, 195 PyPI registry lines, first registry line 13 | RC-31 |
| Lock header on `main` | `revision = 5`, `requires-python = ">=3.15"`, 197 package blocks, 195 PyPI registry lines, first registry line 8 | RC-14, RC-16 |
| Root `requires-dist` versus `pyproject.toml` at the reporter commit | 63 items each. The only difference is the `misthelper-devtools` ref form (`git` table in the lock, `@git+` string in pyproject). | RC-31, RC-42, RC-43, RC-44 |
| Root `requires-dist` versus `pyproject.toml` on `main` | 64 items each. The same single difference. | RC-14, RC-15, RC-18, RC-45, RC-46 |
| `mistapi` pin | `>=0.64.1,<0.65` in both files | RC-18 |
| `uv` dev pin | `==0.13.9` in `pyproject.toml` (line 101) and in the lock (line 1575) on `main` | RC-17, RC-19 |
| Git ref of `misthelper-devtools` | Reporter lock and pyproject both name `e8e093d205428b5503887267b6a9751fa7354be7`. `main` names `2239e7bd468fd27e40c43f2b87fcd35a2e49672b` in both. | RC-43, RC-44 (reporter), and RC-45, RC-46 (main) |

### 1.3 Rejected metadata candidates

| Candidate | Evidence | Verdict |
|---|---|---|
| Registry source index in `uv.lock` versus the configured index | 195 registry source lines name `https://pypi.org/simple`, first at line 8 (RC-14). uv does not reuse a lock that references a registry outside the configuration (RC-36, line 284). The bootstrap compares the first registry line with the configured index (RC-09, RC-10). | Leading hypothesis. Not reproduced live (U-04). |
| Root `requires-dist` versus `pyproject.toml` | Static comparison matches at the reporter commit (63 items) and on `main` (64 items). | Rejected |
| `misthelper-devtools` ref | Both files name the same commit at each point in time. | Rejected |
| Package set | 197 package blocks equal the reporter line `Resolved 197 packages`. | Rejected as a set difference |
| Lock revision header | The reporter lock has `revision = 3`. A uv test comment says a revision 3 lock stays valid until a new resolution is needed (U-09). | Rejected as the sole cause. Revision 5 with uv 0.13.x is untested (U-08). |
| Python requirement | The reporter lock declares `>=3.13` (RC-31). The bootstrap command selects Python 3.15.2 (RC-41). Python 3.15.2 satisfies both minimums. | Rejected |
| uv version | The reporter version is unknown (U-01). The dev pin is 0.13.9 (RC-17). The local machine runs uv 0.13.7. | Unverified |

**Decision**: the metadata that uv rejects is the registry source index, as in D-1. The static checks exclude drift and package-set causes for the reporter lock.

## 2. Index Mechanism

1. The bootstrap reads the pip index through `pip config list` (`scripts/bootstrap_worktree.py`, `PipIndexProbe`, lines 165 to 210).
2. If the configured index answers the probe, the run keeps it (lines 235 to 258).
3. `InstallationPolicy.apply` clears the index variables and maps the pip primary index into `UV_INDEX_URL` and the pip extra index into `UV_EXTRA_INDEX_URL` (lines 404 to 446, RC-04).
4. The locked sync runs with that child environment (line 466, RC-01).
5. uv treats a lock as unusable when the configuration omits a registry that the lock names (RC-36). The lock check then reports "needs to be updated" (RC-08).
6. `diagnose_sync_failure` names the index cause only when the primary index differs from the first registry line (lines 477 to 493).

## 3. CI Evidence on `main`

- Job `Dependency lock and exports` in run 45774119357 (job 139753527647) passed. Its step `uv lock --check` printed `Resolved 197 packages in 1ms` (RC-21, RC-22, RC-39).
- Job `test` in run 45774128095 (job 139753623812) passed. Its step `uv sync --locked --extra dev --no-install-project` printed `Resolved 197 packages` and `Installed 171 packages` (RC-23, RC-40).
- No CI job checked the lock at the reporter commits. The job lists of runs 42188122152, 42282055206, 42288182543, and 42589635262 hold no lock job.
- Interpretation: on GitHub runners with the public index, the lock is current at `main`. The reporter failure needs a condition that the runners lack, such as a configured non-public index (hypothesis A-002).

## 4. Local Environment Observation

This observation does not describe the reporter run (U-03).

- `uv --version` reports `uv 0.13.7` on this Windows machine. The dev pin is 0.13.9.
- `python -m pip config list` reports a primary index setting and an extra index setting. The primary value differs from the public index. The values are withheld.
- The current session holds no environment variable whose name starts with `UV_` or `PIP_`.

## 5. Linked Work

The pull request search for `4591` returned no pull request. The pull requests below come from the issue comments and the commit history. Their state and title were read with `gh pr view --json number,title,state,mergedAt,headRefName`. Their changed files were not read.


| Item | State | Relation to this record |
|---|---|---|
| Issue 4591 | Open. Labels: `bug`, `ci`, `needs-human-review`. | Subject of this record. |
| Issue 4774 | Open | Reports a locked bootstrap failure with a configured pip mirror after the pip sources map into UV variables. This record does not close it. |
| Issue 4876 | Closed 2026-11-22 | The public-lock-index path. PR #4880 closed it. |
| PR 4880 | Merged 2026-11-22, commit `b1360b31674a3e9082c2d4103953bfc01941e786` | Added the uv search, `diagnose_sync_failure`, the cause messages, and `--public-lock-index` (RC-35). |
| PR 4505 | Merged 2026-11-05, commit `c57c9b704c1ce23976228cd72cad80b9d99926be` | Introduced the locked sync (the reporter-era bootstrap). |
| PR 4601 | Merged 2026-11-06 | Generated the locked pip exports (lock blob changed on that day). |
| PR 4616 | Merged 2026-11-06 | Bumped uv from 0.12.5 to 0.13.4 in the lock group. |
| PR 4679 | Merged 2026-11-10 | Bumped uv from 0.13.4 to 0.13.7. |
| PR 4750 | Merged 2026-11-10 | Set the Python 3.15 baseline. |
| PR 4871 | Merged 2026-11-21 | Refreshed and pinned dependencies. |
| PR 4358 | Merged 2026-11-13 | Named in the 2026-11-06 issue comments as a `pyproject.toml` owner. The merged title is `refactor(tests): stage unowned unit-test domain groups`. The merged diff is unchecked. |
| PR 4676 | Merged 2026-11-10 | Updated nodeenv and mypy-extensions. |
| PR 4678 | Closed without merge | Mypy-extensions bump. Not merged. |
| Issues 1866, 2000, 3302 | Closed | Earlier bootstrap work: the virtual environment, the pip probe, and the browser certificate trust. |

## 6. Decisions

### D-1 Rejected metadata

- **Options**:
  - (a) the registry source index in `uv.lock` compared with the configured index.
  - (b) requires-dist drift between `uv.lock` and `pyproject.toml`.
  - (c) the lock revision header.
  - (d) a change in the package set.
- **Chosen**: (a).
- **Reason**: uv rejects a lock that names an omitted registry (RC-36). The bootstrap encodes the same check (RC-05, RC-09, RC-10). The static checks exclude (b), (c), and (d) for the reporter lock (section 1.3).
- **Risk**: the reporter run is not reproduced live (U-01, U-02, U-04).
- **Recommended**: (a).

### D-2 Locked sync policy

- **Options**:
  - (a) keep the locked sync strict and keep `--public-lock-index` as an explicit opt-in.
  - (b) add an automatic frozen sync fallback.
  - (c) make the public index the default for the locked sync.
- **Chosen**: (a).
- **Reason**: the bootstrap states that the locked sync enforces the committed lock (RC-01, comment on line 466). A frozen fallback skips the lock check and hides drift. Option (c) changes the default for every operator with a configured index. The probe history (issue 2000) shows that configured indexes are intended.
- **Risk**: operators with a reachable configured index still pass the flag (issue 4774 stays open).
- **Recommended**: (a).

### D-3 Index variable names in messages

- **Options**: (a) name each active index variable without its value, (b) print the configured index value, or (c) keep the message unchanged.
- **Chosen**: (a). The diagnosis rule stays on the primary index.
- **Reason**: the repository owner asked for the names without host names, URLs, or tokens (issue comment of 2026-11-11). Names carry no host and no credential. Option (b) can expose a credential-bearing URL. Option (c) keeps the gap that the owner reported.
- **Risk**: names alone may not identify an extra-index conflict (U-05).
- **Recommended**: (a).

### D-4 UV_NATIVE_TLS

- **Options**:
  - (a) remove `UV_NATIVE_TLS`, keep `UV_SYSTEM_CERTS=1`, and document uv 0.11.0 as the minimum.
  - (b) keep both variables.
  - (c) set `UV_NATIVE_TLS` only for uv older than 0.11.0.
- **Chosen**: (a).
- **Reason**: uv prints a deprecation warning when `UV_NATIVE_TLS` is set (RC-37). uv added `UV_SYSTEM_CERTS` in 0.11.0 (RC-38). Option (c) needs a version probe in the child path.
- **Risk**: R-01 in `plan.md` (uv older than 0.11.0 ignores `UV_SYSTEM_CERTS`, U-07).
- **Recommended**: (a).

### D-5 Dependency scope

- **Options**: (a) change no dependency file and no lock, (b) regenerate the lock with uv 0.13.9, or (c) pin the uv version inside the bootstrap.
- **Chosen**: (a).
- **Reason**: the issue states that it does not request dependency changes. The static checks show no drift (section 1.2).
- **Risk**: if the reporter failure is drift at another commit, a new check is needed. Gate G-1 provides the data for that check.
- **Recommended**: (a).

### D-6 Test strategy

- **Options**: (a) scripted runs with `ScriptedRun` and `monkeypatch`, with no network, (b) real uv runs in tests, or (c) contract tests only.
- **Chosen**: (a).
- **Reason**: the repository rule requires mocked external responses and no production credential in tests (`AGENTS.md`, section "Tests"). Real uv runs depend on the network and on the platform. Contract tests cannot prove the message names.
- **Risk**: scripted output may differ from real uv output. Task T006 repeats the run live.
- **Recommended**: (a).

### D-7 Documentation

- **Options**: (a) correct `documentation/development-setup.md` in the same change, (b) leave the document stale, or (c) move the bootstrap description to a new file.
- **Chosen**: (a).
- **Reason**: `AGENTS.md` requires documentation updates in the same change. A second description of the bootstrap would drift.
- **Risk**: low. The edit touches four lines.
- **Recommended**: (a).

### D-8 Gate for code changes

- **Options**:
  - (a) gate G-1, which requires reporter data before code.
  - (b) start the change now from the static evidence.
  - (c) mark the decision for human review.
- **Chosen**: (a).
- **Reason**: the owner wrote on 2026-11-07 and 2026-11-11 that no change starts before the UV version and full output arrive. The condition is data, not one of the four human-decision categories in the brief, so the record does not mark it `HUMAN-DECISION-REQUIRED`.
- **Risk**: the change waits on the reporter.
- **Recommended**: (a).

### D-9 Record identity

- **Options**: slug `locked-worktree-bootstrap` or `uv-lock-bootstrap`, size S or M, and labels unchanged or `in-progress` added now.
- **Chosen**: slug `locked-worktree-bootstrap`, size S, labels unchanged.
- **Reason**: the slug matches the issue title. The change touches one script, one test module, and one document. The `in-progress` label belongs to the claim step before the branch exists.
- **Risk**: low.
- **Recommended**: the chosen option.

## 7. Remote Verification

Each row records one check. The row count equals the `remote_checks` count in `META_DIR\4591-STATUS.json` (48 rows). Blob SHAs are taken from the GitHub contents or tree API. Line numbers are taken from the decoded file body.

| No. | Claim | Path | Ref | Blob SHA | Result | Line |
|---|---|---|---|---|---|---|
| RC-01 | Locked sync command, with the comment "Enforce the committed lock." | scripts/bootstrap_worktree.py | main | e16515ffa789cca7d0bdd7e9789898588e5f1312 | present | 466 |
| RC-02 | Child environment sets `UV_NATIVE_TLS` | scripts/bootstrap_worktree.py | main | e16515ffa789cca7d0bdd7e9789898588e5f1312 | present | 417 |
| RC-03 | Child environment sets `UV_SYSTEM_CERTS` | scripts/bootstrap_worktree.py | main | e16515ffa789cca7d0bdd7e9789898588e5f1312 | present | 418 |
| RC-04 | Pip index settings mapped into UV index variables | scripts/bootstrap_worktree.py | main | e16515ffa789cca7d0bdd7e9789898588e5f1312 | present | 446 |
| RC-05 | Diagnosis after a failed sync | scripts/bootstrap_worktree.py | main | e16515ffa789cca7d0bdd7e9789898588e5f1312 | present | 477 |
| RC-06 | Index cause message text | scripts/bootstrap_worktree.py | main | e16515ffa789cca7d0bdd7e9789898588e5f1312 | present | 136 |
| RC-07 | Lock drift message text | scripts/bootstrap_worktree.py | main | e16515ffa789cca7d0bdd7e9789898588e5f1312 | present | 141 |
| RC-08 | Stale phrase constant "needs to be updated" | scripts/bootstrap_worktree.py | main | e16515ffa789cca7d0bdd7e9789898588e5f1312 | present | 153 |
| RC-09 | First registry source reader | scripts/bootstrap_worktree.py | main | e16515ffa789cca7d0bdd7e9789898588e5f1312 | present | 325 |
| RC-10 | Configured index reader (`UV_INDEX_URL`, then `UV_DEFAULT_INDEX`) | scripts/bootstrap_worktree.py | main | e16515ffa789cca7d0bdd7e9789898588e5f1312 | present | 342 |
| RC-11 | Public index option in the parser | scripts/bootstrap_worktree.py | main | e16515ffa789cca7d0bdd7e9789898588e5f1312 | present | 679 |
| RC-12 | Locked sync info log | scripts/bootstrap_worktree.py | main | e16515ffa789cca7d0bdd7e9789898588e5f1312 | present | 467 |
| RC-13 | Wrapper passes `-PublicLockIndex` | scripts/bootstrap_worktree.ps1 | main | 36db3250f4183110584f4bd6d69d1f47ea89aefa | present | 68 |
| RC-14 | Registry source lines: 195, first at line 8 | uv.lock | main | 5445b4eb382dc9f6dd5c351ba40c521f01f93165 | present | 8 |
| RC-15 | Root package block, with 197 package blocks in the file | uv.lock | main | 5445b4eb382dc9f6dd5c351ba40c521f01f93165 | present | 1436 |
| RC-16 | Lock header: `revision = 5`, `requires-python = ">=3.15"` | uv.lock | main | 5445b4eb382dc9f6dd5c351ba40c521f01f93165 | present | 2 |
| RC-17 | Lock `requires-dist` uv pin `==0.13.9` | uv.lock | main | 5445b4eb382dc9f6dd5c351ba40c521f01f93165 | present | 1575 |
| RC-18 | Pyproject `mistapi>=0.64.1,<0.65` | pyproject.toml | main | eca34c826ea44ba4f2faefc07d04c2c117e99751 | present | 29 |
| RC-19 | Pyproject dev pin `uv==0.13.9` | pyproject.toml | main | eca34c826ea44ba4f2faefc07d04c2c117e99751 | present | 101 |
| RC-20 | Pyproject version `2.1.0` | pyproject.toml | main | eca34c826ea44ba4f2faefc07d04c2c117e99751 | present | 3 |
| RC-21 | CI lock check step `uv lock --check` | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 648 |
| RC-22 | CI job name "Dependency lock and exports" | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 635 |
| RC-23 | CI locked sync step in the container build | .github/workflows/container-build.yml | main | 737325976de75e90aa4526ab1cf2978782e648ce | present | 95 |
| RC-24 | Existing test fixture with the stale phrase | tests/unit/scripts/test_bootstrap_worktree_uv.py | main | 568a790c7491684a486010c5bc46c53623f1342f | present | 41 |
| RC-25 | Development setup says the bootstrap installs the requirements files | documentation/development-setup.md | main | 1733975a7e0a0962fe5367e165a21f5831f8c3e5 | stale | 28 |
| RC-26 | Development setup table row for `UV_NATIVE_TLS=1` | documentation/development-setup.md | main | 1733975a7e0a0962fe5367e165a21f5831f8c3e5 | present | 73 |
| RC-27 | Development setup describes `--public-lock-index` | documentation/development-setup.md | main | 1733975a7e0a0962fe5367e165a21f5831f8c3e5 | present | 65 |
| RC-28 | Copilot instructions state `mistapi>=0.64.0,<0.65` | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | stale | 21 |
| RC-29 | Spec route base is 5 | .specify/scripts/powershell/spec-route.ps1 | main | 37293a255f9b5de20ccb2b3ef0ad15717bab2826 | present | 17 |
| RC-30 | No record exists under the route on `main` | specs/numbered/0/0/1/2/1/3/3/1 | main | none (tree listing) | absent | 0 |
| RC-31 | Reporter-era lock: 197 package blocks, `revision = 3`, first registry line 13 | uv.lock | c57c9b704c1ce23976228cd72cad80b9d99926be | 4a1674057b1b139ee95265130c38c88772c49d3b | present | 13 |
| RC-32 | Reporter-era bootstrap runs the locked sync | scripts/bootstrap_worktree.py | c57c9b704c1ce23976228cd72cad80b9d99926be | dd03b30a694697bee0a7ed9be271cd1b4b4b2f86 | present | 281 |
| RC-33 | Bootstrap blob at the main head at issue creation | scripts/bootstrap_worktree.py | 5d444bda23ea50de131d67b6e6fcf37055adfa77 | dd03b30a694697bee0a7ed9be271cd1b4b4b2f86 | present | 281 |
| RC-34 | Lock blob at the main head at issue creation | uv.lock | 5d444bda23ea50de131d67b6e6fcf37055adfa77 | 4a1674057b1b139ee95265130c38c88772c49d3b | present | 13 |
| RC-35 | PR 4880 merge commit holds the index cause message | scripts/bootstrap_worktree.py | b1360b31674a3e9082c2d4103953bfc01941e786 | e16515ffa789cca7d0bdd7e9789898588e5f1312 | present | 136 |
| RC-36 | Upstream uv rule: a lock that names an omitted registry is not reused | crates/uv-lock-operations/src/validated_lock.rs | 9bf01bef71c76643290ca17635970076fab1bd0d | 96add5c58f6373af9076b4bd9f6dfd2ee9767069 | present | 284 |
| RC-37 | Upstream uv deprecation warning for `UV_NATIVE_TLS` | crates/uv-cli/src/settings.rs | 9bf01bef71c76643290ca17635970076fab1bd0d | 415b5317596501da4622ffaa9f671c77112eacf7 | present | 345 |
| RC-38 | Upstream uv `UV_SYSTEM_CERTS` added in 0.11.0 | crates/uv-static/src/env_vars.rs | 9bf01bef71c76643290ca17635970076fab1bd0d | 9a451de47b5b96e0b91e1de0ad012682aa649240 | present | 128 |
| RC-39 | CI lock check passed on run 45774119357 | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 648 |
| RC-40 | CI locked sync passed on run 45774128095 | .github/workflows/container-build.yml | main | 737325976de75e90aa4526ab1cf2978782e648ce | present | 95 |
| RC-41 | Bootstrap command pins Python 3.15.2 | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 29 |
| RC-42 | Reporter-era pyproject: mistapi pin `>=0.64.1,<0.65` | pyproject.toml | c57c9b704c1ce23976228cd72cad80b9d99926be | b698e777ad59c5ea1f9423c5314b9a6f05a69ba2 | present | 29 |
| RC-43 | Reporter-era pyproject: devtools ref `e8e093d205428b5503887267b6a9751fa7354be7` | pyproject.toml | c57c9b704c1ce23976228cd72cad80b9d99926be | b698e777ad59c5ea1f9423c5314b9a6f05a69ba2 | present | 122 |
| RC-44 | Reporter-era lock: devtools requires-dist with rev `e8e093d205428b5503887267b6a9751fa7354be7` | uv.lock | c57c9b704c1ce23976228cd72cad80b9d99926be | 4a1674057b1b139ee95265130c38c88772c49d3b | present | 2157 |
| RC-45 | Main pyproject: devtools ref `2239e7bd468fd27e40c43f2b87fcd35a2e49672b` | pyproject.toml | main | eca34c826ea44ba4f2faefc07d04c2c117e99751 | present | 123 |
| RC-46 | Main lock: devtools requires-dist with rev `2239e7bd468fd27e40c43f2b87fcd35a2e49672b` | uv.lock | main | 5445b4eb382dc9f6dd5c351ba40c521f01f93165 | present | 1532 |
| RC-47 | `configured_index` reads `UV_DEFAULT_INDEX` as the second source | scripts/bootstrap_worktree.py | main | e16515ffa789cca7d0bdd7e9789898588e5f1312 | present | 345 |
| RC-48 | `InstallationPolicy.apply` removes `UV_DEFAULT_INDEX` from the child environment | scripts/bootstrap_worktree.py | main | e16515ffa789cca7d0bdd7e9789898588e5f1312 | present | 409 |

Method notes:

- RC-01 to RC-30, RC-39 to RC-41, and RC-45 to RC-48 are taken from decoded `main` bodies, the tree listing, or the CI job logs.
- RC-31 to RC-34 are taken from the GitHub contents API at the named commit. The line numbers are taken from the local `git show` of the same blob.
- RC-42 to RC-44 are taken from the reporter-era blobs. The blob IDs are taken from the contents API, and the line numbers are taken from `git show` of the same blob.
- RC-35 is taken from the GitHub commits API. The bootstrap blob at that commit is the same as on `main`.
- RC-36, RC-37, and RC-38 are taken from the GitHub contents API for the uv repository at the named commit. The `web_fetch` tool blocked the raw host, so the API read replaced it.
- Line numbers in sections 1 and 2 that have no row were read from the local `HEAD` file. The local blob equals the remote blob (`e16515ff` for `scripts/bootstrap_worktree.py`, `5445b4eb` for `uv.lock`), so the lines match `main`.

## 8. Sources

- S-01: Issue #4591 body and comments, read with `gh issue view 4591 -R jmorrison-juniper/MistHelper --json` on 2026-11-26.
- S-02: `scripts/bootstrap_worktree.py` and `scripts/bootstrap_worktree.ps1` on `main` (RC-01 to RC-13).
- S-03: `uv.lock` and `pyproject.toml` on `main` and at commit `c57c9b704` (RC-14 to RC-20, RC-31, RC-34).
- S-04: `requirements-dev.txt` on `main` (line 470, `uv==0.13.9`, blob `9a528bfe03a10f7bc903f5768ef26de765bbff43`).
- S-05: `.github/workflows/ci.yml` and `.github/workflows/container-build.yml` on `main` (RC-21 to RC-23, RC-39, RC-40).
- S-06: CI run 45774119357 (job 139753527647) and run 45774128095 (job 139753623812), read with `gh run view --job --log`.
- S-07: `.github/copilot-instructions.md` on `main` (RC-28, and line 29 for the Python 3.15.2 command).
- S-08: `documentation/development-setup.md` on `main` (RC-25 to RC-27).
- S-09: `tests/unit/scripts/test_bootstrap_worktree_uv.py` on `main` (RC-24). The local file holds the same blob.
- S-10: `.specify/scripts/powershell/spec-route.ps1` on `main` (RC-29).
- S-11: `.specify/memory/constitution.md` (version 1.9.0), `.specify/templates/*.md`, `AGENTS.md` (blob `44a9afffb5bd6f774973a845d27343e4e528b6ad`), and the reference record `specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv/` (shape only). These files are local and match `main`.
- S-12: uv source at `9bf01bef71c76643290ca17635970076fab1bd0d`, read through `https://api.github.com/repos/astral-sh/uv/contents/crates/uv-lock-operations/src/validated_lock.rs?ref=9bf01bef71c76643290ca17635970076fab1bd0d` (RC-36). The same pattern reads `crates/uv-cli/src/settings.rs` (RC-37) and `crates/uv-static/src/env_vars.rs` (RC-38).
- S-13: PR and issue states, read with `gh pr view` and `gh issue view` on 2026-11-26.
- S-14: Local pip configuration and uv version, read with `python -m pip config list` and `uv --version`. Values are withheld. See section 4.
- S-15: The `web_fetch` tool blocked `raw.githubusercontent.com` for the uv file. No content from that attempt is used.

## 9. Unverified

- U-01: The reporter uv version. The issue does not state it, and comments of 2026-11-07 and 2026-11-11 ask for it.
- U-02: The reporter active index variables. The issue does not state them.
- U-03: The reporter pip configuration. The local machine check does not describe that run.
- U-04: Live reproduction. No uv command ran, because the brief forbids script and tool runs for this record. Task T006 repeats the run.
- U-05: Whether an extra index alone makes uv reject the lock. The uv rule (RC-36) keeps the default index in scope when only an extra index is set. Source reading only.
- U-06: Whether the public index is reachable from the reporter network. The option `--public-lock-index` depends on it.
- U-07: Whether system certificate trust works with a uv older than 0.11.0 after `UV_NATIVE_TLS` is removed. No test ran.
- U-08: Whether uv 0.13.x rejects a revision 3 lock with the default index. No test ran.
- U-09: The uv test comment "Existing revision 3 lockfiles remain valid until a new resolution is needed" (`crates/uv/tests/project/lock.rs`, lines 992 to 1017 at `9bf01bef`). The text is taken from a code search excerpt. The file was not fetched by URL.

## 10. Skills

No local skill was loaded. The issue has no Podman, container, or Juniper device question.

## 11. Documents Read

- `AGENTS.md`, `.github/copilot-instructions.md`, and `.specify/memory/constitution.md`: read in full.
- Spec Kit templates in `.specify/templates/` (spec, plan, tasks, and checklist): read in full.
- Reference record `specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv/`: read for shape only.
- `documentation/development-setup.md`: read at the bootstrap sections (lines 20 to 76 and lines 340 to 365).
- `documentation/quality-gates.md`: read the macOS pip-audit section (lines 252 to 274). It does not conflict with this change.
- `documentation/architecture.md` and `documentation/operator-guide.md`: searched for bootstrap references. The architecture reference names a different package, `src/foundation/runtime/bootstrap`. The operator guide holds no bootstrap reference.
- `documentation/container-deployment.md`: not read. The change starts no container.
