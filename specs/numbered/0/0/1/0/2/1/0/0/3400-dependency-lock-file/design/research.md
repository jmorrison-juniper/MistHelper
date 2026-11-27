# Research: Tracked Dependency Lock File

This file holds each decision, its evidence, the remote verification table, the legacy record check, the local differences, the sources, and the unverified items.

## R0. Method and truth order

- GitHub `main` outranks each local copy. This record reads `main` at commit `f03c6c9b36d612a48d7b9652998c2fd87dd777ca`, committed on 2026-11-26 at 07:15:01 UTC.
- The local HEAD equals that commit. Six working-tree files differ from HEAD in line endings only. Git reports them as unchanged, and this record does not use them as evidence (see R6).
- Each remote check reads the blob SHA with `gh api` and decodes the base64 content. The line number comes from the decoded text.
- The four legacy record files match `main` by blob SHA. Their line numbers come from the local copy.
- No build, test, package install, container, or repository script ran. Git reads used only read commands: `rev-parse`, `status`, `ls-files`, `cat-file`, `hash-object`, `check-attr`, and `config`.

## R1. Issue facts

- Issue #3400 is open. Labels: `ci`, `chore`, `in-progress`, `dependencies`, `workflow`, `needs-human-review`. The issue has 17 comments.
- The issue body dates from 2026-09-25. These body facts are stale on `main`:
  - The body says `.gitignore` line 329 excludes `uv.lock`. `main` has no uv ignore rule (RC-08).
  - The body says 36 runtime entries with one exact pin. `main` has 108 exact pins and no range entry (RC-17).
  - The body says the host runs Python 3.13.3 and the image runs Python 3.13.15. `main` requires Python 3.15 (RC-10). The Dockerfile base is `python:3.15-slim` (RC-32).
  - The body says no commit holds `uv.lock`. `main` tracks it (RC-01).
- Comments that changed the plan:
  - 2026-10-06 20:58 UTC. A read-only assessment recommends option 4.
  - 2026-10-20 02:15 UTC. Option 4 becomes working assumption A-001 in PR #4320.
  - 2026-11-06 06:11 UTC. The repository owner gives go-ahead for the dependency change.
  - 2026-11-17 06:56 UTC. The owner holds the next container slice until a separate approval and a serial-slot assignment.
  - 2026-11-17 06:57 UTC. The prior owner confirms that the hold applies to future S5 slices. The user was unavailable when asked.

## R2. Linked pull requests and overlap

| PR | Title | State | Merged (UTC) | Lock-related files |
|---|---|---|---|---|
| #4320 | docs(spec): plan the tracked dependency lock migration | Merged | 2026-10-20 04:31 | Legacy record folder: plan, spec, tasks |
| #4325 | chore(deps): reconcile pyproject declarations and add parity guard | Merged | 2026-10-20 05:00 | `pyproject.toml`, declaration parity guard |
| #4326 | chore(deps): add the first tracked uv.lock and lock guard | Merged | 2026-10-20 05:30 | `.gitignore`, `uv.lock`, lock guard |
| #4505 | chore(bootstrap): sync worktree dependencies from uv.lock | Merged | 2026-11-05 16:45 | `scripts/bootstrap_worktree.py`, bootstrap tests (path moved, see RC-55) |
| #4601 | chore(deps): generate locked pip exports | Merged | 2026-11-06 08:30 | `requirements.txt`, `requirements-dev.txt`, `uv.lock`, export guard |
| #4820 | ci: enforce dependency lock and export checks | Merged | 2026-11-17 06:08 | `.github/workflows/ci.yml`, workflow guard |
| #4851 | ci(container): run container unit tests from the dependency lock | Merged | 2026-11-19 22:22 | `.github/workflows/container-build.yml`, trigger guard |
| #258 | deps(ops-portal): bump zustand from 5.0.11 to 5.0.12 | Merged | 2026-05-07 20:59 | Not linked. It matched the search text. Its files are under `ops-portal/`. |

The open-PR scan on 2026-11-26 found seven open PRs. Three change dependency files:

- PR #4888 changes `requirements-dev.txt`. On 2026-11-26, 30 of its checks report FAILURE. They include `Dependency lock and exports`, `pip-audit (CVE scan)`, `Ruff (ops platform)`, and `Test quality ratchet (gate)` (RC-59).
- PRs #4889 and #4890 change `mist-ops-platform/requirements.txt`. Task T020 changes the same file, so T020 waits until both PRs merge or close.

## R3. Decisions

Each decision names the alternatives, the chosen option, the reason, and the risk. No decision needs a person's authority under section 6 of the brief.

### D-1. Track `uv.lock`, keep `pyproject.toml` canonical, and export for pip

- Alternatives: (a) keep lower bounds and resolve on each install. (b) Add `uv.lock` before the declarations were complete. (c) Add a pip-compile lock with `.in` sources. (d) Track `uv.lock` from a canonical `pyproject.toml`, which is option 4 of the 2026-10-06 assessment.
- Chosen: (d).
- Rationale: The lock and both exports exist and pass their guards (RC-01 to RC-06, RC-16 to RC-18). The issue body measured drift on 2026-09-25. The owner gave go-ahead on 2026-11-06. Option (c) adds a second resolver. The constitution already names uv as the preferred installer and requires `requirements.txt` for pip (RC-47).
- Risk: Mixed install paths remain until decisions D-3 to D-7 land. Each path has a task.
- Human decision required: no.

### D-2. Keep `pip-audit -r requirements.txt` on the runtime export

- Alternatives: (a) keep the current command. (b) Use `pip-audit --locked .`, which the legacy plan proposed.
- Chosen: (a).
- Rationale: The runtime export holds the exact runtime set (RC-16, RC-17). The quality-gates document says to keep this command in `ci.yml` (RC-45). Option (b) widens the audit to development packages and uses a tool flag that this record did not verify.
- Risk: Development-only packages stay outside the audit. This matches the current state.
- Human decision required: no.

### D-3. Install CI packages through a locked uv sync

- Alternatives: (a) keep `pip install -r` from the exports. (b) Add a composite action under `.github/actions/`. (c) Prefix each command with `uv run`.
- Chosen: each CI job that installs packages runs `python -m pip install uv==0.13.9`. The job then runs `uv sync --locked --extra dev --no-install-project`. It then appends the project `.venv/bin` folder to `GITHUB_PATH`.
- Rationale: The 2026-10-06 assessment states that managed paths use the lock. The `GITHUB_PATH` step keeps the existing `python -m` commands unchanged. All jobs run on `ubuntu-latest` (RC-24). A composite action adds a direct child under `.github`, which already holds 14 children (RC-51). Option (c) edits every command.
- Risk: Caution: a wrong PATH step fails each job that uses it. Mitigation: one slice, contract cases c5 and c6, pull request CI, and no force push.
- Human decision required: no.

### D-4. Install the image runtime set with a locked uv sync

- Alternatives: (a) keep `pip install -r requirements.txt` from the export. (b) Copy a uv binary from a digest-pinned uv image. (c) Export hashes and install with `--require-hashes`.
- Chosen: the image runs `uv sync --locked --no-install-project` with `UV_PROJECT_ENVIRONMENT=/opt/misthelper-venv`, with uv 0.13.9 installed and removed in the same `RUN` step. The build context must admit `uv.lock`, which the root `.dockerignore` excludes today (RC-09).
- Rationale: The image then reads the lock, not a derived file. The lock stores sha256 values (RC-06). The export carries no hashes (RC-16). The image already disables dependency auto-upgrade (RC-34). Option (b) needs a verified digest that this record did not read. Option (c) changes the export format and the export guard.
- Risk: Warning: a pushed image tag can reach users before anyone checks its package set. Mitigation: freeze comparison case c10, and a dispatch run only after the user approves it. Unverified items U-C and U-K name the open parts.
- Human decision required: no.

### D-5. Give `mist-ops-platform` its own `uv.lock`

- Alternatives: (a) a uv workspace with the root lock. (b) Keep the `uv pip compile` output. (c) Defer the ops lock.
- Chosen: (d) a separate `mist-ops-platform/uv.lock`.
- Rationale: Both ops containers install the project from `pyproject.toml` without a lock (RC-37, RC-38). The ops export header names one Windows interpreter (RC-39), so it does not show the Linux set. A workspace couples the root and ops releases. Deferring leaves the ops containers unlocked.
- Consequence: The new lock adds a direct child to `mist-ops-platform/`, which holds 11 children (RC-52). Complexity Tracking in plan.md records this Principle I exception.
- Risk: The exception stays until follow-up F-2 restructures the ops folder.
- Human decision required: no.

### D-6. Use one uv version with a `required-version` range

- Alternatives: (a) `required-version = "==0.13.9"`, which needs a pyproject edit for each patch release. (b) No `required-version`, with the bootstrap installing the latest uv.
- Chosen: `[tool.uv]` with `required-version = ">=0.13.9,<0.14"` in `pyproject.toml`. The pin stays at line 101 (RC-14). The bootstrap and the container build use the same literal, and case c4 compares them.
- Rationale: The uv source compares the running version with `required-version` and reports a mismatch. Source: `astral-sh/uv` at commit `9bf01bef71c76643290ca17635970076fab1bd0d`, file `crates/uv-settings/src/lib.rs`, lines 247 to 261. The bootstrap installs uv without a pin (RC-29).
- Risk: A developer with uv 0.14 receives a version error from uv until the range changes.
- Human decision required: no.

### D-7. Dependabot uses the uv ecosystem

- Alternatives: (a) keep the `pip` ecosystem, which edits exports directly. (b) A bot commit that regenerates the exports after each Dependabot update. (c) pip-compile `.in` pairs.
- Chosen: the `uv` ecosystem for `/` and `/mist-ops-platform`. The export guard names the regeneration command. A maintainer runs that command when the guard fails.
- Rationale: The current `pip` entry edits exports directly, and PR #4888 fails the lock and export checks (RC-35, RC-59). The 2026-10-06 assessment reports native `uv.lock` updater support in Dependabot. This record did not reread that source (unverified item U-N). Option (b) adds a write path from an automated pull request, which this record does not approve. Option (c) adds a second resolver.
- Risk: Each Dependabot lock update needs one manual export step (follow-up F-1).
- Human decision required: no.

### D-8. Base image digest pinning is out of scope

- Alternatives: (a) pin the base digest in this issue. (b) File a follow-up issue.
- Chosen: (b).
- Rationale: The lock fixes Python package versions only. The base tag `python:3.15-slim` names mutable content (RC-33). The docker-build skill states that a tag is mutable and that a digest identifies fixed content. It also states that a pinned base alone does not pin a package repository or network download. It also states that an unchanged `RUN apt-get update` command can reuse an old result (skill file `01-containerfiles-and-input-contexts/07-base-images-and-input-pinning.md`).
- Risk: The image stays partly mutable until the follow-up issue lands.
- Human decision required: no.

### D-9. Reuse the legacy record folder

- Alternatives: (a) a new slug, which creates a second record for one issue in the same route. (b) Reuse the folder and replace its files. (c) Leave the legacy files unchanged.
- Chosen: (b). The folder keeps the slug `dependency-lock-file`.
- Rationale: The brief allows reuse after steps 3 and 4, which this record completes in R4 and R5. Option (c) keeps stale claims (R5).
- Consequence: `design/lock-comparison.md` is deleted, because the `design` folder may hold five children only. Its facts move to this file.
- Human decision required: no.

### D-10. The record pull request uses `Refs #3400`

- Alternatives: (a) `Closes #3400`, which the brief requires for T-PR. (b) `Refs #3400`. The final slice uses `Closes #3400`.
- Chosen: (b).
- Rationale: The owner states that the issue stays open until the remaining slices and required validation finish (comment of 2026-11-09 17:41 UTC). A closing keyword on the record pull request closes the issue at merge, before those slices finish.
- Risk: The brief's T-PR rule is not met literally. Analysis item A-13 records the deviation.
- Human decision required: no.

## R4. Remote verification table

Each row is one remote check. Ref is `main` for every row. Result values are present, absent, partial, or stale. A line of 0 means that the claim concerns the whole path or the tree.

| ID | Claim | Path | Blob SHA | Result | Line |
|---|---|---|---|---|---|
| RC-01 | `uv.lock` is tracked and has lock version 1 | `uv.lock` | 5445b4eb382dc9f6dd5c351ba40c521f01f93165 | present | 1 |
| RC-02 | `uv.lock` requires Python 3.15 | `uv.lock` | 5445b4eb382dc9f6dd5c351ba40c521f01f93165 | present | 3 |
| RC-03 | `uv.lock` resolves mistapi 0.64.1 from the public index | `uv.lock` | 5445b4eb382dc9f6dd5c351ba40c521f01f93165 | present | 1419 |
| RC-04 | `uv.lock` pins misthelper-devtools to commit 2239e7bd | `uv.lock` | 5445b4eb382dc9f6dd5c351ba40c521f01f93165 | present | 1586 |
| RC-05 | `uv.lock` holds 197 package tables | `uv.lock` | 5445b4eb382dc9f6dd5c351ba40c521f01f93165 | present | 5 |
| RC-06 | `uv.lock` stores sha256 values in 1295 lines | `uv.lock` | 5445b4eb382dc9f6dd5c351ba40c521f01f93165 | present | 9 |
| RC-07 | `uv.lock` stores an exclude-newer option | `uv.lock` | 5445b4eb382dc9f6dd5c351ba40c521f01f93165 | absent | 0 |
| RC-08 | `.gitignore` ignores `uv.lock` (issue body line 329) | `.gitignore` | 17eadfadb35a59e191a61c78877569ad747ddcc7 | absent | 0 |
| RC-09 | `.dockerignore` admits `uv.lock` into the image build context | `.dockerignore` | 4fc430ad7046ec61f6f64d9658bda2567f84c09d | absent | 121 |
| RC-10 | `pyproject.toml` requires Python 3.15 | `pyproject.toml` | eca34c826ea44ba4f2faefc07d04c2c117e99751 | present | 23 |
| RC-11 | `pyproject.toml` declares mistapi `>=0.64.1,<0.65` | `pyproject.toml` | eca34c826ea44ba4f2faefc07d04c2c117e99751 | present | 29 |
| RC-12 | `pyproject.toml` enables direct references for Hatch | `pyproject.toml` | eca34c826ea44ba4f2faefc07d04c2c117e99751 | present | 167 |
| RC-13 | `pyproject.toml` pins misthelper-devtools to commit 2239e7bd | `pyproject.toml` | eca34c826ea44ba4f2faefc07d04c2c117e99751 | present | 123 |
| RC-14 | `pyproject.toml` pins `uv==0.13.9` in its optional dependencies table | `pyproject.toml` | eca34c826ea44ba4f2faefc07d04c2c117e99751 | present | 101 |
| RC-15 | `pyproject.toml` has a `[tool.uv]` table with `required-version` | `pyproject.toml` | eca34c826ea44ba4f2faefc07d04c2c117e99751 | absent | 0 |
| RC-16 | `requirements.txt` is an exact uv export without hashes | `requirements.txt` | 50fe63d4cf5e6071612c62c288e965190c60b969 | present | 2 |
| RC-17 | `requirements.txt` holds 108 exact pins and no range entry | `requirements.txt` | 50fe63d4cf5e6071612c62c288e965190c60b969 | present | 129 |
| RC-18 | `requirements-dev.txt` is an exact uv export for the dev extra | `requirements-dev.txt` | 9a528bfe03a10f7bc903f5768ef26de765bbff43 | present | 2 |
| RC-19 | `requirements-dev.txt` pins `uv==0.13.9` | `requirements-dev.txt` | 9a528bfe03a10f7bc903f5768ef26de765bbff43 | present | 470 |
| RC-20 | The `dependency_lock` job runs `uv lock --check` | `.github/workflows/ci.yml` | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 648 |
| RC-21 | The `dependency_lock` job runs the export guard | `.github/workflows/ci.yml` | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 650 |
| RC-22 | Every CI Python install uses a locked uv sync | `.github/workflows/ci.yml` | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | absent | 234 |
| RC-23 | The `pip_audit` job runs `pip-audit -r requirements.txt` | `.github/workflows/ci.yml` | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 498 |
| RC-24 | CI jobs run on `ubuntu-latest` | `.github/workflows/ci.yml` | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 636 |
| RC-25 | The container build trigger includes `uv.lock` | `.github/workflows/container-build.yml` | 737325976de75e90aa4526ab1cf2978782e648ce | present | 13 |
| RC-26 | The container unit tests run with `uv sync --locked` | `.github/workflows/container-build.yml` | 737325976de75e90aa4526ab1cf2978782e648ce | present | 95 |
| RC-27 | The container build reads `./Containerfile` | `.github/workflows/container-build.yml` | 737325976de75e90aa4526ab1cf2978782e648ce | present | 113 |
| RC-28 | The container build has an image freeze comparison | `.github/workflows/container-build.yml` | 737325976de75e90aa4526ab1cf2978782e648ce | absent | 0 |
| RC-29 | The bootstrap pins the uv version it installs | `scripts/bootstrap_worktree.py` | e16515ffa789cca7d0bdd7e9789898588e5f1312 | absent | 457 |
| RC-30 | The bootstrap runs `uv sync --locked --extra dev` | `scripts/bootstrap_worktree.py` | e16515ffa789cca7d0bdd7e9789898588e5f1312 | present | 466 |
| RC-31 | The Dockerfile installs the runtime set with a locked uv sync | `Dockerfile` | bc9249a19f6f181e7ea0e2c4b565a139d16d9253 | absent | 120 |
| RC-32 | The Containerfile installs the runtime set with a locked uv sync | `Containerfile` | bc9249a19f6f181e7ea0e2c4b565a139d16d9253 | absent | 120 |
| RC-33 | The Dockerfile base image pins a digest | `Dockerfile` | bc9249a19f6f181e7ea0e2c4b565a139d16d9253 | absent | 22 |
| RC-34 | The Dockerfile sets `AUTO_UPGRADE_DEPENDENCIES=false` | `Dockerfile` | bc9249a19f6f181e7ea0e2c4b565a139d16d9253 | present | 168 |
| RC-35 | The root Dependabot entry uses the `uv` ecosystem | `.github/dependabot.yml` | be5ad1ea473a41662c2d225a174daa8a6f95df84 | absent | 3 |
| RC-36 | `mist-ops-platform/uv.lock` exists | `mist-ops-platform/uv.lock` | none (path absent) | absent | 0 |
| RC-37 | The ops API container installs from a lock | `mist-ops-platform/deploy/Containerfile.api` | b108429aba3dac1d4b60b34cec85c59f7acc25f1 | absent | 28 |
| RC-38 | The ops worker container installs from a lock | `mist-ops-platform/deploy/Containerfile.worker` | 4163badd829f90927fbc15aedadf2b975ea44890 | absent | 28 |
| RC-39 | The ops `requirements.txt` is a cross-platform lock | `mist-ops-platform/requirements.txt` | 8daf95a15558f8dffbf4f892f8eaf9f1acb30e07 | absent | 2 |
| RC-40 | `documentation/development-setup.md` documents the export regeneration command | `documentation/development-setup.md` | 1733975a7e0a0962fe5367e165a21f5831f8c3e5 | absent | 0 |
| RC-41 | A guard asserts that `.gitignore` keeps `uv.lock` tracked | `tests/guardrails/test_dependency_lock_file.py` | 1e398e42c443073ae7df64984e3da298df345395 | absent | 0 |
| RC-42 | `.github/copilot-instructions.md` states the mistapi floor that `pyproject.toml` declares | `.github/copilot-instructions.md` | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | stale | 21 |
| RC-43 | `documentation/development-setup.md` describes the bootstrap as a requirements install | `documentation/development-setup.md` | 1733975a7e0a0962fe5367e165a21f5831f8c3e5 | stale | 28 |
| RC-44 | `documentation/container-deployment.md` lists `uv.lock` among the image trigger files | `documentation/container-deployment.md` | f06228bc6bbe77cc009f956403872a06462466ea | stale | 291 |
| RC-45 | `documentation/quality-gates.md` keeps `pip-audit -r requirements.txt` in `ci.yml` | `documentation/quality-gates.md` | 6776d334cca5d9b43273473a06da367a65605c6d | present | 275 |
| RC-46 | The constitution requires Python 3.15 | `.specify/memory/constitution.md` | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 278 |
| RC-47 | The constitution requires `requirements.txt` for pip compatibility | `.specify/memory/constitution.md` | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 298 |
| RC-48 | `AGENTS.md` defines the Simplified Technical English writing style | `AGENTS.md` | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 40 |
| RC-49 | `spec-route.ps1` uses base 5 for numeric routes | `.specify/scripts/powershell/spec-route.ps1` | 37293a255f9b5de20ccb2b3ef0ad15717bab2826 | present | 17 |
| RC-50 | The local gates table lists the Tests row | `.github/copilot-instructions.md` | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 61 |
| RC-51 | The `.github` folder holds five or fewer direct children | `.github` (tree count of 14) | none (tree count) | absent | 0 |
| RC-52 | `mist-ops-platform` holds five or fewer direct children | `mist-ops-platform` (tree count of 11) | none (tree count) | absent | 0 |
| RC-53 | The declaration parity guard holds the declaration and Python floor tests | `tests/guardrails/test_dependency_declaration_parity.py` | 51e24f5e98fbf78af50eb6bb91513776db8aa838 | present | 133 |
| RC-54 | The export guard holds the export match test | `tests/guardrails/test_dependency_export.py` | a2a3e279dbfefb5292923d745cffa4ea4c66654d | present | 101 |
| RC-55 | The bootstrap test holds the locked sync test at its moved path | `tests/unit/config/foundation/runtime/startup/bootstrap/dependency/test_uv_locked_sync.py` | 678632eec13c5673cbc453210d47a09bacf8b431 | present | 29 |
| RC-56 | The workflow guard holds the lock gate test | `tests/guardrails/test_dependency_lock_workflow.py` | e529b5c8dc2ce363c670a42595070135fac230c4 | present | 74 |
| RC-57 | The trigger guard holds the locked test environment test | `tests/guardrails/test_container_build_trigger.py` | 48c4e62b67df372e2f26a900d3b4df3f47a8a612 | present | 153 |
| RC-58 | The lock guard holds the lock currency test | `tests/guardrails/test_dependency_lock_file.py` | 1e398e42c443073ae7df64984e3da298df345395 | present | 78 |
| RC-59 | Open Dependabot PR #4888 passes the lock and export checks | `pull request #4888` | none (pull request) | absent | 0 |
| RC-60 | The legacy `spec.md` states that `requirements.txt` has 37 range-only entries | `specs/numbered/0/0/1/0/2/1/0/0/3400-dependency-lock-file/spec.md` | 718fa3a0f8fc63b4af4b0d03c9560c71a1634f13 | stale | 29 |
| RC-61 | The legacy `spec.md` states that `pyproject.toml` omits 16 runtime packages | `specs/numbered/0/0/1/0/2/1/0/0/3400-dependency-lock-file/spec.md` | 718fa3a0f8fc63b4af4b0d03c9560c71a1634f13 | stale | 31 |
| RC-62 | The legacy `lock-comparison.md` states that the lock stores the date in an `[options]` table | `specs/numbered/0/0/1/0/2/1/0/0/3400-dependency-lock-file/design/lock-comparison.md` | 833ad0bc1ec2de6ed1a4569d3282b2a21dd412ca | stale | 8 |
| RC-63 | The legacy `lock-comparison.md` states that the lock holds 197 packages | `specs/numbered/0/0/1/0/2/1/0/0/3400-dependency-lock-file/design/lock-comparison.md` | 833ad0bc1ec2de6ed1a4569d3282b2a21dd412ca | present | 13 |
| RC-64 | The legacy `tasks.md` statuses for T001 to T024 are readable | `specs/numbered/0/0/1/0/2/1/0/0/3400-dependency-lock-file/tasks.md` | 4bfe0b7a1f5897b782a9a6ac16617df9c408429a | present | 5 |

Counts: 64 remote checks. Results: 38 present, 20 absent, 6 stale. The STATUS file and the summary use the same count.

## R5. Legacy record check

The legacy folder holds `spec.md`, `plan.md`, `tasks.md`, and `design/lock-comparison.md`. The brief requires a reuse check (section 3, steps 3 and 4). Each legacy task receives one result. Verified means that `main` agrees with the legacy status. Stale means that `main` contradicts the legacy claim. Absent means that the claimed item is not on `main` and cannot be found in this checkout.

| Legacy task | Legacy status | Evidence on `main` | Result |
|---|---|---|---|
| T001 Write `spec.md` | Done | File exists (RC-60 cites its text) | verified |
| T002 Write `plan.md` | Done | File exists | verified |
| T003 Write `tasks.md` | Done | File exists (RC-64) | verified |
| T004 Open the S0 pull request and post the assumption | Done | PR #4320 merged on 2026-10-20. Comment on 2026-10-20 02:15 UTC | verified |
| T005 Reconcile declarations | Done | RC-10, RC-11, RC-53 | verified |
| T006 Enable Hatch direct references | Done | RC-12 | verified |
| T007 Add the parity guard and its failing fixture | Done | RC-53 | verified |
| T008 Capture `dependency-freeze-before.txt` | Done | Git-ignored artifact. Not on `main`. Not present in this checkout | absent |
| T009 Generate `uv.lock` with a baseline `--exclude-newer` date | Done | RC-07. The lock holds no exclude-newer option | stale |
| T010 Compare the lock with the freeze | Done | Comparison file exists. RC-63 matches the count of 197 | verified |
| T011 Remove the ignore lines and add the lock guard | Done | RC-08, RC-58 | verified |
| T012 Switch the bootstrap to `uv sync --locked` | Done | RC-30 | verified |
| T013 Update the bootstrap unit and contract tests | Done | RC-55 at the moved path | verified |
| T014 Generate the exports from the lock | Done | RC-16, RC-18 | verified |
| T015 Add the export drift guard | Done | RC-54 | verified |
| T016 Switch each CI and container install to the lock | Open | RC-22 (CI still installs with pip). RC-26 (container tests use the lock) | verified |
| T017 Add the `dependency_lock` job and switch the audit | Open | RC-20 (job exists). RC-23 (audit still reads `requirements.txt`) | verified |
| T018 Update the workflow contract tests | Open | RC-56 exists. CI install cases do not exist | verified |
| T019 Switch `Dockerfile` and `Containerfile` | Open | RC-31, RC-32 | verified |
| T020 Compare the image package lists | Open | RC-28 | verified |
| T021 Change the Dependabot root entry to `uv` | Open | RC-35 | verified |
| T022 Document the export regeneration command | Open | RC-40 (no regeneration command in the setup document) | verified |
| T023 Add a lock for `mist-ops-platform` | Open | RC-36 | verified |
| T024 Close #3400 only when T005 to T023 pass | Open | Issue is open (R1) | verified |

Counts: 22 verified, 1 stale (T009), 1 absent (T008). These counts appear in STATUS as `existing_record`.

## R6. Local working tree differences

Git reports the local HEAD as `f03c6c9b36d612a48d7b9652998c2fd87dd777ca`. `git status --porcelain` lists five modified files that this issue does not touch. They are `src/foundation/support/utils/logger_utils.py`, `src/interfaces/wan_performance/collection/request_admission.py`, `src/mist/intelligence/reports/subscription_expiry/client.py`, `tests/unit/marvis/mist/intelligence/reports/audits/credentials/subscription_expiry/test_client.py`, and `tests/unit/wan_dashboard/wan_performance/collection/test_request_admission.py`. This record does not use them.

The six files below have CRLF line endings in the working tree and LF line endings in the committed blob. The root `.gitattributes` sets `* text=auto` at line 2. For each file, the working-tree byte count minus its CR count equals the HEAD blob size. Git's filtered hash equals the HEAD blob. Git therefore reports these files as unchanged. Line numbers do not change.

| Path | HEAD blob | Raw working-tree blob | Filtered blob (git view) | Git status |
|---|---|---|---|---|
| `uv.lock` | 5445b4eb | a13aadfe | 5445b4eb | Unchanged |
| `.gitignore` | 17eadfad | fb94d3f6 | 17eadfad | Unchanged |
| `Dockerfile` | bc9249a1 | afdbdac3 | bc9249a1 | Unchanged |
| `Containerfile` | bc9249a1 | afdbdac3 | bc9249a1 | Unchanged |
| `mist-ops-platform/deploy/Containerfile.api` | b108429a | e8b72b07 | b108429a | Unchanged |
| `mist-ops-platform/deploy/Containerfile.worker` | 4163badd | 5f13d34a | 4163badd | Unchanged |

The implementation slices start from `main`, not from this checkout. Stage named files only, so no commit includes an unrelated local change.

## R7. Sources

Local paths (all read-only):

- `AGENTS.md` (line 17 for the role, line 40 for the writing style).
- `.github/copilot-instructions.md` (local gates table at lines 57 to 76, and the instruction section for Python and uv).
- `.specify/memory/constitution.md` (Principles I to VII and the technology constraints).
- `.specify/templates/spec-template.md`, `plan-template.md`, `tasks-template.md`, and `checklist-template.md` (headings for this record).
- `specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv/` (reference record). Its `spec.md`, `tasks.md`, `analysis.md`, `design/research.md`, and `design/checklists/requirements.md` gave the shape. No content was copied.
- `documentation/quality-gates.md` (lines 252 to 280, the pip-audit note).
- `documentation/container-deployment.md` (lines 284 to 296, the trigger list).
- `specs/numbered/0/0/1/0/2/1/0/0/3400-dependency-lock-file/` (legacy record, read in full).
- `.specify/scripts/powershell/spec-route.ps1` (route base at line 17).

Remote sources:

- GitHub `main` at commit `f03c6c9b36d612a48d7b9652998c2fd87dd777ca`, read through `gh api` (trees and contents).
- Issue #3400 and the linked pull requests, read through `gh issue view` and `gh pr view`.
- Issues #1779, #1866, #3397, #3399, #3959, #4255, #4622, #4727, #4785, and #4811 were checked for state. All are closed. Records for issues #4785 and #4811 exist under `specs/` in the tree.

Skill and external sources:

- Skill `docker-build`, file `C:\Users\jmorrison\.agents\skills\docker-build\01-containerfiles-and-input-contexts\07-base-images-and-input-pinning.md`. It supports D-8.
- `astral-sh/uv` at commit `9bf01bef71c76643290ca17635970076fab1bd0d`, file `crates/uv-settings/src/lib.rs`, lines 247 to 261, and `crates/uv-settings/src/settings.rs`, lines 35 to 76. These lines show the `required-version` check. It supports D-6. The source was read through the semantic code search tool.

No Mist API endpoint and no mistapi function appear in this record. The only mistapi fact is the pinned version (RC-03, RC-11).

## R8. Unverified

These items do not have evidence that this record can cite. The plan does not depend on them as facts. Each item names the task that verifies it.

- U-A: Whether `uv sync` verifies the sha256 values in the lock during an install. The record makes no claim. Owner: none.
- U-B: Whether the `GITHUB_PATH` step works for all 28 CI commands. The record relies on the PR CI run. Owner: T-REMOTE-CI.
- U-C: Whether `uv sync --no-install-project` in the image needs `README.md`, which `pyproject.toml` names at line 5. Owner: T016 acceptance.
- U-D: Whether the mist-ops container build contexts include `uv.lock` and `pyproject.toml`. Those workflow contexts were not read. Owner: T019.
- U-E: Whether Dependabot tokens can push a commit. The record does not claim it. Owner: none. The record avoids the bot commit option.
- U-F: Why each of the 30 failing checks on PR #4888 fails, as of 2026-11-26. The record cites only the lock and export failure (RC-59). Owner: the PR author.
- U-G: Whether the 2026-11-17 publication hold ended. No issue comment after 06:57 UTC records an end. PR #4851 merged on 2026-11-19. Owner: the user, before each slice publication.
- U-H: Whether the git-ignored `test-artifacts/dependency-freeze-before.txt` existed on another machine. It is absent from this checkout. Owner: none.
- U-I: Whether the ops `requirements.txt` differs from a Linux resolution. The header names a Windows interpreter (RC-39). The difference was not measured. Owner: T020.
- U-J: Whether the export hash omission changes pip behavior. The record does not claim a change. Owner: follow-up issue.
- U-K: Whether the `misthelper` user (UID 1000) can read `/opt/misthelper-venv`. Owner: T016 acceptance, image run.
- U-L: Whether `pip-audit --locked` exists in the pinned version 2.10.1 (RC-19 pins pip-audit in the dev export). The record does not use the flag. Owner: none.
- U-M: Whether issue #3959, the coordinator ledger, holds current guidance. Its state is closed (R1). Owner: none.
- U-N: Whether the Dependabot uv ecosystem reads `uv.lock` in the form the 2026-10-06 assessment describes. Owner: T023.
