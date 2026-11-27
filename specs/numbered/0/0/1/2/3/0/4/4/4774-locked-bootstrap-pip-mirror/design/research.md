# Research: Locked Bootstrap With a Configured Pip Index

## 1. Method

- Remote truth: GitHub `main` at commit `f03c6c9b36d612a48d7b9652998c2fd87dd777ca` (`gh api repos/jmorrison-juniper/MistHelper/git/ref/heads/main`).
- The full tree was read once. It holds 11404 entries and is not truncated.
- Each cited line came from the decoded file body (for example, `gh api repos/jmorrison-juniper/MistHelper/contents/uv.lock?ref=main`).
- Local HEAD equals main for every cited blob. The worktree diff against HEAD is empty for the planned files (R86).
- No build, test, linter, formatter, install, container, or repository script ran. uv behavior comes from owner comments and from the uv documentation.
- Two web reads cover the uv documentation (R84 and R85).
- Row numbers R01 to R93 match the order of `remote_checks` in `4774-STATUS.json`.

## 2. Issue facts (Step 1)

- Title: `Runtime: locked bootstrap fails with a configured pip mirror`.
- State: OPEN. Labels: `bug`, `ci`. Author: `jmorrison-juniper`.
- Created 2026-11-11T21:44:21Z. Updated 2026-11-16T00:21:14Z.
- Summary: the isolated worktree bootstrap fails during the locked sync when it maps a configured pip mirror into UV settings. `uv lock --check --offline` exits 0. `uv sync --locked --extra dev` exits 0 when run directly. The owner states that the offline lock check does not reproduce the bootstrap environment (comment 6807911629).
- Error text, quoted from the issue body:
  - `error: The lockfile at uv.lock needs to be updated, but --locked was provided.`
  - `hint: To update the lockfile, run uv lock.`
  - `The locked UV sync failed with code 1.`
  - `The bootstrap failed: The locked UV sync failed with code 1.`
- Reproduction steps in the issue: run `uv lock --check --offline`, run `uv sync --locked --extra dev`, and run the bootstrap with the configured index set.
- Comments:
  - Comment 6807911629 (2026-11-11, owner). The issue relates to #4591. The current main maps pip `index-url` and `extra-index-url` into `UV_INDEX_URL` and `UV_EXTRA_INDEX_URL`. Keep the issue open. Do not change `uv.lock` or dependency manifests. Record the UV version and the setting names. Do not contact the private mirror.
  - Comment 6847333228 (2026-11-13, owner). Windows verification on UV 0.13.7. The setting names are `global.index-url` and `global.extra-index-url`. The bootstrap failed with the stale-lock error. No dependency or bootstrap change was made.
  - Comment 6848025890 (2026-11-13, owner). The bootstrap also failed in the issue 2746 worktree.
  - Comment 6903867178 (2026-11-16, owner). A synthetic two-index test on macOS. Table: UV 0.12.23, 0.13.7, and 0.13.8. Changing `UV_INDEX_URL` gives a stale lock with exit 1. Adding `UV_EXTRA_INDEX_URL` passes. With UV 0.13.8, a locked install fetched the package from the locked primary, not the extra index. Blocker: the owner policy must define the permitted source behavior before a repair.

## 3. Existing record (Step 3)

- Local search: no folder under `specs\` starts with `4774-`. The recursive glob and the recursive directory search both returned nothing.
- Meta folder: no file starts with `4774`.
- DRAFT_DIR was empty before this run.
- Remote search: no path under `specs/` matches `4774-`, and route `0/0/1/2/3/0/4/4` is absent (R75).
- Result: `existing_record.found` is false.

## 4. Linked work (Step 2)

- `gh pr list --search 4774 --state all`: no pull request.
- Related issues (read with `gh api repos/jmorrison-juniper/MistHelper/issues/<n>`):

| Issue | State | Labels | Relation to 4774 |
| - | - | - | - |
| #4591 | open | bug, ci, needs-human-review | Same symptom, reported on Windows. Comment 6807911629 names it as related. |
| #4773 | open | feature, web-portal, in-progress | The issue body says no bootstrap source change is in #4773. |
| #2746 | open | chore, tests, in-progress, priority:P3, severity:medium | Comment 6848025890 reports the same failure in its worktree. |
| #4876 | closed | bug, scripts | Prior fix. Code comments cite #4876 for the public lock option and the mismatch text (R28). |
| #3399 | closed | ci, chore, performance | Introduced the uv installer and the source mapping (R77). |
| #2000 | closed | chore, production-readiness | Introduced the probe for an unreachable configured index. |
| #4255 | closed | security, tests, in-progress | Pip security fragment. No overlap with the source mapping. |

- Open pull requests checked for file overlap (AGENTS parallel-agents rule, R06): 4890, 4889, 4888, 4887, 4886, 4813, and 4208. Pull request 4888 changes `requirements-dev.txt`, which this change does not edit. No open pull request changes a planned path.

## 5. Code findings (Step 5)

- Root cause path (R34, R35, R36):
  - `InstallationPolicy.apply` calls `_effective_sources` at line 425.
  - `_effective_sources` sets `UV_INDEX_URL` to the configured primary index at line 446.
  - `sync` runs `uv sync --locked --extra dev` at line 466.
- Lock state (R43, R44): all 195 registry lines name `https://pypi.org/simple`. No other registry line exists.
- Diagnosis (R38, R30): the mismatch branch at line 491 names the configured index only when the lock check reports a stale lock.
- Other mapping sites: `git grep` at HEAD for `UV_INDEX|UV_EXTRA_INDEX|UV_DEFAULT_INDEX` found matches only in `scripts/bootstrap_worktree.py` and its tests. No match exists in `src/` (R93). The runtime package `src/foundation/runtime/bootstrap/` holds no index mapping (D-8).
- Existing tests that encode the old mapping: R51, R52, R53, R55, and R57.
- Module docstring: line 20 states the old stop behavior (R28).
- Documentation: R66 states the stop on mismatch. R67 and R68 describe the primary mapping as intended.
- Working-tree line counts from `Get-Content` differed from remote counts. The blob SHAs match (R86), so the remote line numbers apply.
- Top-level names in the module: five classes and twelve functions (R40).
- Mist API and mistapi: not applicable. The bootstrap has no mistapi reference (R41). The OpenAPI file and the mistapi source were not read for this issue.
- Reviewed without dependency: `documentation/architecture.md` (package list) and `documentation/quality-gates.md` (gate procedures). No claim in this record depends on either file.
- Mistapi pin: pyproject states `>=0.64.1,<0.65` (R47). requirements states `0.64.1` (R48). The development guide states `0.64.0` (R89). The constitution states `0.59+` (R27). D-11 tracks the drift.

## 6. Decisions (Step 6)

### D-1 (HUMAN-DECISION-REQUIRED): Index policy for the locked sync when the configured index differs from the lock

- Category: credential policy (brief section 6). A configured index can carry credentials. The index policy sets the trust boundary for installed packages. The owner reserved this decision in comment 6903867178.
- Options:
  - Option A: keep the configured index as the uv primary index. The locked sync fails by design when the index differs. Operators pass `--public-lock-index`. This is the current behavior (R35, R36, R39).
  - Option B: map the configured index to the uv extra index. Keep the lock registry as primary. The owner observed passing lock checks on UV 0.12.23, 0.13.7, and 0.13.8 (comment 6903867178). uv gives the default index the lowest priority and uses `first-index` by default (R84). A package on the configured index would then win over PyPI in any resolution. On UV 0.13.8, a locked sync with an empty cache fetched the package from the index that the lock names, not the extra index. The owner concludes that mapping the configured primary to an extra index does not preserve the primary source policy (comment 6903867178).
  - Option C: use the lock registry only for the locked sync. Keep the configured index for pip steps. Recommended.
  - Option P: route downloads through the configured index with a uv proxy index. The proxy feature is in preview (R84). It needs a uv configuration file in the child and a mirror layout that matches PyPI artifact paths (U-5).
- Recommended: option C.
- Reasons:
  1. Every registry line in the lock names PyPI (R43, R44). The lock never requires the configured index.
  2. `--locked` installs the URLs that the lock records (R84 proxy section and R85). A changed index does not alter installed files.
  3. Option C reuses the tested public-lock path (R33, R39, R59). It adds no configuration file.
  4. Option C removes the `first-index` risk of option B.
  5. The lock check no longer depends on the configured index.
- Risk:
  - Caution: the configured index no longer affects uv. Pip steps still use it.
  - Caution: if public PyPI is blocked, the locked sync fails with a network error, not a lock error.
  - Mitigation: the Caution line (FR-004), the guide text (FR-013), and the owner check (SC-002).
- Owner action: approve option C, or select another option. Comment 6903867178 forbids ignoring or remapping a configured primary, weakening `--locked`, transforming the lock, or contacting a private mirror to bypass this decision. Option C does not pass the configured index to the locked sync, so implement it only after approval. Tasks T011 through T015 wait for the answer.

### D-2: Keep the locked sync and the lock check. Do not edit `uv.lock` or any dependency manifest

- Alternatives: (a) regenerate a lock for the configured registry. Rejected: the owner forbids a lock change (comment 6807911629), and a per-index lock forks the project. (b) Switch to `--frozen`. Rejected: the check that detects lock drift disappears.
- Chosen: keep `--locked` (R36) and the dependency lock step (R61).
- Risk: none new.

### D-3: Keep the `--public-lock-index` name. Update its help text

- Alternatives: (a) remove the option. Rejected: the PowerShell wrapper passes it (R42), and the bootstrap help documents it (R39). (b) Keep the current help text. Rejected: the text says the default differs, which stops being true.
- Chosen: keep the name. Update the help text (T014).
- Risk: under option C the option repeats the default. Caution: removing the option later breaks scripts that pass it. D-11 tracks any removal.

### D-4: Tests use stubs and a loopback listener only

- Alternatives: (a) a private mirror. Rejected: the owner forbids it (comment 6807911629). (b) Public PyPI. Rejected: network dependence and nondeterminism. (c) Stubs with a socket guard. Chosen.
- Chosen: TST-02 stubs `fallback_index` and fails on any socket connection. The quickstart uses a loopback listener on 127.0.0.1 port 8765.
- Risk: stubs cannot prove uv behavior. The quickstart Q3 check and owner check SC-002 cover that gap.

### D-5: Write the failing tests first

- Alternatives: (a) code first, then tests. Rejected: a test that passes after the code change does not prove the defect. (b) Tests and code together. Rejected for the same reason.
- Chosen: T004 through T010 precede T011 through T015. FR-015 requires each behavior test to fail on main.
- Risk: the first cycle takes longer. The test list changes when D-1 changes.

### D-6: Rewrite or remove the assertions that encode the old mapping

- Alternatives: (a) keep the assertions and add exceptions. Rejected: the tests would keep the defect as expected behavior. (b) Delete the tests. Rejected: the tests also protect the caller environment and the fallback.
- Chosen: TST-07, TST-08, and TST-09 rewrite the assertions (R51, R53, R55). The precedence test (R52) and the mismatch test (R57) are removed.
- Risk: expected values change. Reviewers compare each change in the pull request.

### D-7: Update the setup guide and the module docstring in the same change

- Alternatives: (a) a separate documentation issue. Rejected: the constitution documentation section (R24) keeps the guide with the behavior. (b) Leave the docstring stale. Rejected: R28 states the old stop behavior.
- Chosen: T013 updates the docstring. T015 updates the guide.
- Risk: none new.

### D-8: Limit the code change to the bootstrap script, two test files, the guide, and the changelog

- Alternatives: (a) also change `src/foundation/runtime/bootstrap/`. Rejected: no index mapping exists there (R93 and section 5). (b) Change `scripts/bootstrap_worktree.ps1`. Rejected: it passes flags only (R42).
- Chosen: the limited scope.
- Risk: none.

### D-9: Remove the two unreachable names and record the symbol-diff exception

- Alternatives: (a) keep both names as unused constants. Rejected: dead code and a stale message would remain. (b) Rename them. Rejected: the rename gives no reader benefit.
- Chosen: remove `INDEX_MISMATCH_MESSAGE` (R30) and `configured_index` (R32). The symbol gate reports both names. The pull request records the exception. The scripted-edit rule (R05) asks for the removed-line count.
- Risk: the symbol gate fails by design. Mitigation: the exception appears in the pull request body.

### D-10: Keep the Windows verification manual with the owner

- Alternatives: (a) add a Windows CI job. Rejected: the job spends runner time, and the owner host can run the check. (b) Skip the Windows check. Rejected: the defect was observed on Windows (comment 6847333228).
- Chosen: SC-002. The owner records the UV version, the setting names, and the commit SHA on issue #4774.
- Risk: manual evidence can drift from the code. Mitigation: the owner records the commit SHA with the result.

### D-11: File separate issues for the mistapi pin drift and the module size

- Alternatives: (a) fix both in this change. Rejected: each issue holds one concern. (b) Leave both undocumented. Rejected: the drift persists.
- Chosen: file separate issues. Link them in the pull request body.
- Evidence: R27 (0.59 or newer), R47 (>=0.64.1), R48 (0.64.1), R89 (0.64.0), R40 (module names).
- Risk: more issues to track.

### D-12: Use the slug, branch, commit subject, and changelog name below

- Slug: `locked-bootstrap-pip-mirror`.
- Branch: `fix/4774-locked-bootstrap-pip-mirror` (R03 pattern).
- Commit subject: `fix(bootstrap): keep the locked sync on the lock registry` (R18 types).
- Changelog: `changelog.d/issue-4774-locked-bootstrap-pip-mirror.md` (R11 naming rule, R65 guard).
- Alternatives: (a) `docs` or `chore` type. Rejected: the change fixes a defect. (b) A timestamp record. Rejected: numeric records use the route (R10).
- Risk: none.

### D-13: Labels: add `needs-human-review` now. Add `in-progress` at claim time

- Alternatives: (a) add `in-progress` now. Rejected: the claim happens before the branch starts (R12). (b) Add no label. Rejected: the owner decision must stay visible.
- Chosen: `labels_to_add` holds `needs-human-review`. Issue #4591 uses this label (gh api, 2026-11-26). The owner removes the label after D-1 is decided.
- Risk: label hygiene. Mitigation: the owner removes the label after the decision.

### D-14: Read the registry from `uv.lock`, and fail closed when none exists

- Alternatives: (a) hard-code `PUBLIC_INDEX_URL`. Rejected: it fails silently if the lock registry changes. (b) Let uv use its default index when no registry exists. Rejected: it hides a broken lock.
- Chosen: `read_lock_registry` (R31) returns the first registry line. `sync` stops when the result is None (T011).
- Risk: the first-line rule ignores a second registry. TST-05 guards the repository state.

## 7. Remote verification table (Step 4)

Ref `main` means commit `f03c6c9b36d612a48d7b9652998c2fd87dd777ca`. Line 0 means a file-level or absence check.

| # | Claim | Path | Ref | Blob SHA | Result | Line |
| - | - | - | - | - | - | - |
| R01 | AGENTS code quality section: refactor and compatibility shim rules | AGENTS.md | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 73 |
| R02 | AGENTS writing style section (STE rules) | AGENTS.md | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 40 |
| R03 | AGENTS branch rule: type, issue, and slug | AGENTS.md | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 192 |
| R04 | AGENTS pull request rule: body names the closed issue | AGENTS.md | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 224 |
| R05 | AGENTS scripted edit rule: compare module-level names and list removed lines | AGENTS.md | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 162 |
| R06 | AGENTS parallel-agents rule: check open pull requests for file overlap | AGENTS.md | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 244 |
| R07 | AGENTS specifications rule: three or more files need a specification | AGENTS.md | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 345 |
| R08 | Local gates table starts | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 50 |
| R09 | Bootstrap runs uv sync --locked --extra dev | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 36 |
| R10 | Numeric records use the fixed base-5 route | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 160 |
| R11 | Changelog fragment naming rule | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 452 |
| R12 | Status label in-progress for claimed issues | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 440 |
| R13 | Pull request title check reports the Conventional Commits title | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 501 |
| R14 | Constitution Principle I: Five-Item Rule | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 38 |
| R15 | Constitution Principle II: Class-Based Architecture | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 91 |
| R16 | Constitution managed specs roots and numbered route rule | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 57 |
| R17 | Constitution Principle III: Safety-First | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 113 |
| R18 | Constitution Principle IV: Full Deployment Pipeline | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 143 |
| R19 | Constitution Principle V: ASCII-only logs | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 182 |
| R20 | Constitution Principle VI: inline comments | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 204 |
| R21 | Constitution Principle VII: action logging | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 235 |
| R22 | Constitution technology and compatibility constraints | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 274 |
| R23 | Constitution security findings: fix over suppress | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 373 |
| R24 | Constitution documentation section | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 398 |
| R25 | Constitution complexity-driven SpecKit escalation | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 420 |
| R26 | Constitution multi-agent git workflow | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 453 |
| R27 | Constitution mistapi rule states version 0.59 or newer (drift) | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 279 |
| R28 | Module docstring states the stop on index mismatch | scripts/bootstrap_worktree.py | main | e16515ffa789cca7d0bdd7e9789898588e5f1312 | present | 20 |
| R29 | PUBLIC_INDEX_URL constant is https://pypi.org/simple | scripts/bootstrap_worktree.py | main | e16515ffa789cca7d0bdd7e9789898588e5f1312 | present | 82 |
| R30 | INDEX_MISMATCH_MESSAGE constant | scripts/bootstrap_worktree.py | main | e16515ffa789cca7d0bdd7e9789898588e5f1312 | present | 136 |
| R31 | read_lock_registry reads the first registry line of uv.lock | scripts/bootstrap_worktree.py | main | e16515ffa789cca7d0bdd7e9789898588e5f1312 | present | 325 |
| R32 | configured_index reads UV_INDEX_URL | scripts/bootstrap_worktree.py | main | e16515ffa789cca7d0bdd7e9789898588e5f1312 | present | 344 |
| R33 | use_public_lock_index writes the public index to UV_INDEX_URL | scripts/bootstrap_worktree.py | main | e16515ffa789cca7d0bdd7e9789898588e5f1312 | present | 354 |
| R34 | apply() calls _effective_sources | scripts/bootstrap_worktree.py | main | e16515ffa789cca7d0bdd7e9789898588e5f1312 | present | 425 |
| R35 | _effective_sources maps the configured primary index into UV_INDEX_URL | scripts/bootstrap_worktree.py | main | e16515ffa789cca7d0bdd7e9789898588e5f1312 | present | 446 |
| R36 | Locked sync command uses --locked and --extra dev | scripts/bootstrap_worktree.py | main | e16515ffa789cca7d0bdd7e9789898588e5f1312 | present | 466 |
| R37 | STALE_LOCK_TEXT phrase decides the stale verdict | scripts/bootstrap_worktree.py | main | e16515ffa789cca7d0bdd7e9789898588e5f1312 | present | 153 |
| R38 | diagnose_sync_failure returns the index mismatch message | scripts/bootstrap_worktree.py | main | e16515ffa789cca7d0bdd7e9789898588e5f1312 | present | 491 |
| R39 | --public-lock-index option is defined | scripts/bootstrap_worktree.py | main | e16515ffa789cca7d0bdd7e9789898588e5f1312 | present | 679 |
| R40 | Module top-level names: five classes and twelve functions (existing violation) | scripts/bootstrap_worktree.py | main | e16515ffa789cca7d0bdd7e9789898588e5f1312 | present | 156 |
| R41 | Bootstrap script has no mistapi reference | scripts/bootstrap_worktree.py | main | e16515ffa789cca7d0bdd7e9789898588e5f1312 | absent | 0 |
| R42 | Windows wrapper passes --public-lock-index through | scripts/bootstrap_worktree.ps1 | main | 36db3250f4183110584f4bd6d69d1f47ea89aefa | present | 68 |
| R43 | 195 registry lines name https://pypi.org/simple | uv.lock | main | 5445b4eb382dc9f6dd5c351ba40c521f01f93165 | present | 8 |
| R44 | No registry line names another index | uv.lock | main | 5445b4eb382dc9f6dd5c351ba40c521f01f93165 | absent | 0 |
| R45 | pyproject requires-python is >=3.15 | pyproject.toml | main | eca34c826ea44ba4f2faefc07d04c2c117e99751 | present | 23 |
| R46 | pyproject dev optional extra is defined | pyproject.toml | main | eca34c826ea44ba4f2faefc07d04c2c117e99751 | present | 98 |
| R47 | pyproject mistapi pin is >=0.64.1 and <0.65 | pyproject.toml | main | eca34c826ea44ba4f2faefc07d04c2c117e99751 | present | 29 |
| R48 | requirements.txt pins mistapi 0.64.1 | requirements.txt | main | 50fe63d4cf5e6071612c62c288e965190c60b969 | present | 129 |
| R49 | Local installed mistapi is 0.64.1 (dist-info present) | .venv\Lib\site-packages\mistapi-0.64.1.dist-info | local | not applicable: local environment directory | present | 0 |
| R50 | test_existing_uv_runs_one_locked_sync asserts the locked command (KT-01) | tests/unit/config/foundation/runtime/startup/bootstrap/dependency/test_uv_locked_sync.py | main | 678632eec13c5673cbc453210d47a09bacf8b431 | present | 29 |
| R51 | test_pip_index_maps_to_uv_and_preserves_caller_settings asserts the configured index as UV_INDEX_URL (TST-07) | tests/unit/config/foundation/runtime/startup/bootstrap/dependency/test_uv_locked_sync.py | main | 678632eec13c5673cbc453210d47a09bacf8b431 | present | 211 |
| R52 | test_pip_source_precedence_maps_to_uv expects configured sources as UV_INDEX_URL (removed) | tests/unit/config/foundation/runtime/startup/bootstrap/dependency/test_uv_locked_sync.py | main | 678632eec13c5673cbc453210d47a09bacf8b431 | present | 336 |
| R53 | test_unreachable_index_uses_the_public_source_for_both_tools asserts UV_INDEX_URL after apply at line 236 (TST-08) | tests/unit/config/foundation/runtime/startup/bootstrap/dependency/test_uv_locked_sync.py | main | 678632eec13c5673cbc453210d47a09bacf8b431 | present | 220 |
| R54 | test_fallback_keeps_the_caller_environment_and_private_settings_unchanged keeps config files and redacts credentials (KT-02) | tests/unit/config/foundation/runtime/startup/bootstrap/dependency/test_uv_locked_sync.py | main | 678632eec13c5673cbc453210d47a09bacf8b431 | present | 242 |
| R55 | test_each_sync_invocation_uses_a_fresh_source_decision asserts no inherited UV_INDEX_URL at line 163 (TST-09) | tests/unit/config/foundation/runtime/startup/bootstrap/dependency/test_uv_locked_sync.py | main | 678632eec13c5673cbc453210d47a09bacf8b431 | present | 163 |
| R56 | Import of INDEX_MISMATCH_MESSAGE | tests/unit/scripts/test_bootstrap_worktree_uv.py | main | 568a790c7491684a486010c5bc46c53623f1342f | present | 25 |
| R57 | test_sync_names_an_index_mismatch_without_the_mirror_address asserts the mismatch message (removed) | tests/unit/scripts/test_bootstrap_worktree_uv.py | main | 568a790c7491684a486010c5bc46c53623f1342f | present | 268 |
| R58 | test_sync_names_lock_drift_when_the_indexes_match asserts LOCK_DRIFT_MESSAGE (KT-03) | tests/unit/scripts/test_bootstrap_worktree_uv.py | main | 568a790c7491684a486010c5bc46c53623f1342f | present | 273 |
| R59 | test_public_lock_index_points_only_this_run_at_the_public_index (KT-04) | tests/unit/scripts/test_bootstrap_worktree_uv.py | main | 568a790c7491684a486010c5bc46c53623f1342f | present | 325 |
| R60 | _write_lock helper writes a registry line | tests/unit/scripts/test_bootstrap_worktree_uv.py | main | 568a790c7491684a486010c5bc46c53623f1342f | present | 78 |
| R61 | Dependency lock step runs uv lock --check (KT-08) | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 648 |
| R62 | MYPY_PATHS scope excludes scripts | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 93 |
| R63 | Container build runs the locked sync | .github/workflows/container-build.yml | main | 737325976de75e90aa4526ab1cf2978782e648ce | present | 95 |
| R64 | Container trigger guard requires the locked sync line (KT-07) | tests/guardrails/test_container_build_trigger.py | main | 48c4e62b67df372e2f26a900d3b4df3f47a8a612 | present | 86 |
| R65 | Changelog guard test requires a heading and a bullet (KT-06) | tests/guardrails/test_changelog_fragment_policy.py | main | dbd5e8776797f12536b3bc2bd613143b85f3fc4a | present | 192 |
| R66 | Development guide paragraph states the stop on index mismatch | documentation/development-setup.md | main | 1733975a7e0a0962fe5367e165a21f5831f8c3e5 | present | 63 |
| R67 | Development guide Package sources section | documentation/development-setup.md | main | 1733975a7e0a0962fe5367e165a21f5831f8c3e5 | present | 95 |
| R68 | Development guide states uv keeps its default source-resolution policy | documentation/development-setup.md | main | 1733975a7e0a0962fe5367e165a21f5831f8c3e5 | present | 105 |
| R69 | Operator guide names no bootstrap command | documentation/operator-guide.md | main | 60d28f9ea461fc8798973d1d1b7e40491c27c248 | absent | 0 |
| R70 | Container deployment page names no bootstrap command | documentation/container-deployment.md | main | f06228bc6bbe77cc009f956403872a06462466ea | absent | 0 |
| R71 | Git ignores /test-artifacts/ | .gitignore | main | 17eadfadb35a59e191a61c78877569ad747ddcc7 | present | 107 |
| R72 | STE tool section exists | .ste-linter.toml | main | d9f28ef8faf4a4c36a4e967d5b978f96eb306253 | present | 14 |
| R73 | Get-SpecRadixSegments computes the numbered route | .specify/scripts/powershell/spec-route.ps1 | main | 37293a255f9b5de20ccb2b3ef0ad15717bab2826 | present | 4 |
| R74 | Route base is five | .specify/scripts/powershell/spec-route.ps1 | main | 37293a255f9b5de20ccb2b3ef0ad15717bab2826 | present | 17 |
| R75 | Route specs/numbered/0/0/1/2/3/0/4/4 and any specs path with 4774- are absent | specs (route and legacy paths) | main | not applicable: no matching path | absent | 0 |
| R76 | Parent specs/numbered/0/0/1/2/3/ holds five children and gains none | specs/numbered/0/0/1/2/3/ | main | not applicable: directory | present | 0 |
| R77 | Prior decision maps the selected primary source to UV_INDEX_URL | specs/3399-uv-bootstrap/research.md | main | 1cd035b0c70f9f84b35f6fe982e6617c0c01d9d4 | present | 116 |
| R78 | Prior contract sets UV_INDEX_URL to PyPI for the public fallback | specs/3399-uv-bootstrap/contracts/bootstrap-installation.md | main | 6c569a60da3b8ba4b0b5c0693c1630184924295d | present | 156 |
| R79 | Reference checklist heading shape | specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv/design/checklists/requirements.md | main | 4a53b89939bb523902efeaaffd1d7b12221c717b | present | 1 |
| R80 | Spec template exists | .specify/templates/spec-template.md | main | 083ef123c7a2e56e21f3062173fb003258f927e2 | present | 0 |
| R81 | Plan template exists | .specify/templates/plan-template.md | main | 1a54553bd85cbef2178aa55efbeeb0c1942ffdde | present | 0 |
| R82 | Tasks template exists | .specify/templates/tasks-template.md | main | 7e5170324d41a6736c498d6b9fc83651f31d0778 | present | 0 |
| R83 | Checklist template exists | .specify/templates/checklist-template.md | main | 806657da09d1058823923e346a323b633114971a | present | 0 |
| R84 | uv index docs: default index lowest priority, first-index default, legacy --index-url is the default index, --extra-index-url adds indexes, proxy indexes keep lock URLs | https://docs.astral.sh/uv/concepts/indexes/ | web | not applicable: fetched web page | present | 0 |
| R85 | uv sync docs: --locked raises an error instead of updating the lock | https://docs.astral.sh/uv/concepts/projects/sync/ | web | not applicable: fetched web page | present | 0 |
| R86 | Local HEAD blob for the bootstrap script equals main, and the worktree equals HEAD | scripts/bootstrap_worktree.py | local HEAD f03c6c9b36d612a48d7b9652998c2fd87dd777ca | e16515ffa789cca7d0bdd7e9789898588e5f1312 | present | 0 |
| R87 | Text search for lock registry at HEAD in specs, documentation, changelog.d, AGENTS.md, and .github finds no match | specs, documentation, changelog.d, AGENTS.md, .github | local HEAD f03c6c9b36d612a48d7b9652998c2fd87dd777ca | not applicable: text search | absent | 0 |
| R88 | test_sync_keeps_the_original_error_when_the_lock_has_no_fault keeps the original failure (KT-05) | tests/unit/scripts/test_bootstrap_worktree_uv.py | main | 568a790c7491684a486010c5bc46c53623f1342f | present | 285 |
| R89 | Development guide requirements table states mistapi 0.64.0 (drift) | documentation/development-setup.md | main | 1733975a7e0a0962fe5367e165a21f5831f8c3e5 | present | 14 |
| R90 | apply() sets UV_NO_CONFIG to 1 for each child | scripts/bootstrap_worktree.py | main | e16515ffa789cca7d0bdd7e9789898588e5f1312 | present | 419 |
| R91 | apply() removes UV_CONFIG_FILE from each child | scripts/bootstrap_worktree.py | main | e16515ffa789cca7d0bdd7e9789898588e5f1312 | present | 424 |
| R92 | apply() removes the competing uv index aliases UV_INDEX, UV_DEFAULT_INDEX, UV_INDEX_URL, and UV_EXTRA_INDEX_URL | scripts/bootstrap_worktree.py | main | e16515ffa789cca7d0bdd7e9789898588e5f1312 | present | 408 |
| R93 | No UV index alias or mapping appears under src at HEAD (text search for UV_INDEX, UV_EXTRA_INDEX, and UV_DEFAULT_INDEX) | src | local HEAD f03c6c9b36d612a48d7b9652998c2fd87dd777ca | not applicable: text search | absent | 0 |

Row count: 93. The `remote_checks` array in `4774-STATUS.json` holds the same 93 rows in the same order.

## 8. Sources

- Local files at HEAD `f03c6c9b36d612a48d7b9652998c2fd87dd777ca`:
  - `AGENTS.md`
  - `.github\copilot-instructions.md`
  - `.specify\memory\constitution.md`
  - `.specify\templates\spec-template.md`, `plan-template.md`, `tasks-template.md`, `checklist-template.md`
  - `.specify\scripts\powershell\spec-route.ps1`
  - `specs\numbered\0\0\1\2\4\1\4\0\4920-ex-hardware-inventory-csv` (shape only)
  - `documentation\development-setup.md`, `quality-gates.md`, `operator-guide.md`, `container-deployment.md`
  - `scripts\bootstrap_worktree.py`, `scripts\bootstrap_worktree.ps1`
  - `tests\unit\config\foundation\runtime\startup\bootstrap\dependency\test_uv_locked_sync.py`
  - `tests\unit\scripts\test_bootstrap_worktree_uv.py`
  - `tests\guardrails\test_container_build_trigger.py`, `test_changelog_fragment_policy.py`
  - `uv.lock`, `pyproject.toml`, `requirements.txt`
  - `specs\3399-uv-bootstrap\research.md`, `contracts\bootstrap-installation.md`
  - `.venv\Lib\site-packages\mistapi-0.64.1.dist-info` (local environment only)
- Web (fetched in this session):
  - https://docs.astral.sh/uv/concepts/indexes/ (two pages)
  - https://docs.astral.sh/uv/concepts/projects/sync/
- GitHub (read-only `gh` calls):
  - Issue 4774 and comments 6807911629, 6847333228, 6848025890, 6903867178
  - Issues 4591, 4773, 2746, 4876, 3399, 2000, 4255
  - Pull request search for 4774 (no result), and open pull requests 4890, 4889, 4888, 4887, 4886, 4813, 4208
  - Main commit `f03c6c9b36d612a48d7b9652998c2fd87dd777ca`

## 9. Skills

No skill was loaded. The listed skills cover Podman, Juniper devices, Docker products, and similar topics. None covers uv, pip, or the Windows bootstrap script.

## 10. Unverified

- U-1: The owner uv results (UV 0.12.23, 0.13.7, and 0.13.8) come from comment 6903867178. This session did not reproduce them, because the brief forbids running tools.
- U-2: The owner Windows failure text (comments 6847333228 and 6848025890) is not reproduced.
- U-3: The owner output printed the generic failure text, not the mismatch text (comment 6847333228). Current code (R38) names the mismatch when the stale phrase appears and the configured index differs. The owner may have run older code. This is unresolved.
- U-4: Whether `uv sync --locked` checks index URLs beyond the primary. The uv sync page (R85) describes project metadata only. How an extra index affects the lock check, when the mirror lacks a locked version, is not reproduced.
- U-5: Whether the owner mirror serves files at PyPI artifact paths. This is the proxy prerequisite (R84). The host is private, and comment 6807911629 forbids a request.
- U-6: The pip output format for `global.index-url` keys. The parser depends on it. The tests model the format, and pip was not run.
- U-7: PyPI reachability from the owner host. This session cannot check the owner network.
- U-8: The environment names `UV_INDEX_URL` and `UV_EXTRA_INDEX_URL` map to the legacy options. R84 names the options. The names come from the code and from the owner tests (comment 6903867178).
- U-9: Owner UV version 0.13.7 for the Windows run (comment 6847333228). Not verified locally.
