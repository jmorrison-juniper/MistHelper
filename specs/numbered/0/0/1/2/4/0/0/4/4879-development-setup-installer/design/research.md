# Research: Development setup installer text

Each decision lists the choice, the alternatives, the rationale, and the risk. Remote facts come from GitHub `main` at commit `f03c6c9b` (2026-11-26T07:15:01Z), read with `gh api` and `gh pr` in read-only mode. Local files match the remote blobs for each file that the record cites (R-02 and R-14).

## Decisions

### D-1. Scope of the text change

- **Decision**: Edit Step 2 (lines 28 and 29) and the three installer subsections. Keep all other sections unchanged.
- **Alternatives**: (a) Edit only the section that the issue names. (b) Rewrite the whole page.
- **Rationale**: Step 2 introduces the install flow that the installer section explains. Package sources and Browser and account checks describe the child processes of the same flow. Option (a) leaves Step 2 stale (R-03). Option (b) adds review load and no defect.
- **Risk**: The diff is larger than the issue names. The change map in `plan.md` and the checks TST-002 to TST-007 limit the review.
- **Human decision**: No.

### D-2. Keep the manual install path

- **Decision**: Keep lines 132 to 144 unchanged. They show `python -m pip install -r requirements.txt -r requirements-dev.txt` and `uv pip install` as manual steps.
- **Alternatives**: (a) Delete the manual path. (b) Move it to a separate page.
- **Rationale**: The manual commands run without the bootstrap, and they remain valid. The issue targets the bootstrap text only. The heading "To build the environment by hand instead" already separates the manual path.
- **Risk**: A reader may confuse the manual path with the bootstrap. The heading keeps the separation.
- **Human decision**: No.

### D-3. List every setting in the table

- **Decision**: The settings table names twelve settings (plan M-05 and M-06). It keeps the four existing rows, and it adds eight rows with conditions.
- **Alternatives**: (a) Keep the four rows and link to the contract file. (b) List only the settings that the bootstrap sets for every child process.
- **Rationale**: The issue requires each environment setting that the script still sets (issue body, expected behavior). A repository contract file is an implementer aid, not a reader aid. Option (b) hides the public-index settings that the issue expects.
- **Risk**: The table grows. Each row uses one short purpose sentence.
- **Human decision**: No.

### D-4. Remove the extra-source order claim

- **Decision**: Delete line 103, "Extra-source order remains unchanged."
- **Alternatives**: (a) Keep the sentence. (b) Rewrite it as a limit.
- **Rationale**: The parser stores one value for each source key (`scripts/bootstrap_worktree.py` line 206, R-32). No test or run confirms the order of several extra index lines (U-6). A limit belongs in a follow-up issue, not in the reader guide.
- **Risk**: A future reader loses an intended statement. `analysis.md` finding A-04 records the reason.
- **Human decision**: No.

### D-5. Leave the source sweep out of the guide

- **Decision**: Do not document `StaleSourceSweeper` in this change. The contract file (section 2, row 0) lists it, so a reviewer sees it.
- **Alternatives**: (a) Document the sweep in the installer section. (b) Document it in a separate issue, and keep this change narrow.
- **Rationale**: The sweep is not an installer step. It removes cache-only directories under `src`, and its warning needs a separate review. The guide change must stay narrow.
- **Risk**: A reader does not learn that setup removes orphan directories. The recommended separate issue closes that gap. This agent does not file issues, under rule 4 of the brief.
- **Human decision**: No.

### D-6. Add no new pytest case

- **Decision**: Verify the change with the local STE gate, the existing guard `tests/guardrails/test_container_policy_docs.py`, and the commands TST-001 to TST-010 in `design/quickstart.md`.
- **Alternatives**: (a) Add cases to `tests/unit/scripts/test_bootstrap_worktree_uv.py`. (b) Add a guardrail under `tests/guardrails/`.
- **Rationale**: The change is documentation only. It adds no behavior, and no product code path changes. Documentation-only changes need no new test unless a documentation test already names the file. The guard at `tests/guardrails/test_container_policy_docs.py` line 63 names the guide, and it runs in T-LOCAL-GATES.
- **Risk**: The wording can drift again without a guard (A-09). The contract file and a follow-up issue cover that risk.
- **Human decision**: No.

### D-7. Leave the CI STE file list unchanged

- **Decision**: Do not add the guide to the `files:` list of `.github/workflows/ste-lint.yml` (line 44).
- **Alternatives**: (a) Add the guide to the list. (b) Check the score locally only.
- **Rationale**: The issue asks for a local `ste-linter` score of 80 or above. A workflow change alters a shared CI job, and it may create a new required failure. A separate issue can add the guide after the score is known.
- **Risk**: CI does not grade the guide (R-35). The local gate and T-REMOTE-CI cover this risk for this change.
- **Human decision**: No.

### D-8. Add one changelog fragment

- **Decision**: Add `changelog.d/issue-4879-development-setup-installer.md` with one `###` heading and one `- **Fixed**:` bullet.
- **Alternatives**: (a) Add no fragment, and state the internal-only reason in the pull request body, as `changelog.d/README.md` line 58 allows (R-41).
- **Rationale**: The constitution states that each change MUST add one unique fragment (line 409, R-44). It also states that it supersedes practice documents when a conflict arises (line 529, R-45). The internal-only exemption belongs to a practice document, so the constitution takes precedence. The fragment name uses the issue form, because the pull request does not exist yet (`changelog.d/README.md` line 27).
- **Risk**: The release notes gain one entry for a contributor guide. The entry is short, and the release coordinator can review it.
- **Human decision**: No.

### D-9. Branch name and labels

- **Decision**: Use the branch `fix/4879-development-setup-installer`. Add the labels `bug` and `in-progress`. Keep the label `docs`.
- **Alternatives**: (a) Use `docs/4879-development-setup-installer`. (b) Use the type label `chore`.
- **Rationale**: The MistHelper branch rule lists `fix`, `feat`, and `chore` as branch prefixes (`.github/copilot-instructions.md`, branch naming section). The `bug` label marks a wrong statement, and the issue already carries the `docs` scope label. The repository has all three labels (GitHub label list, read on 2026-11-26).
- **Risk**: The maintainer may prefer another label. The orchestrator applies the labels, and it may change them.
- **Human decision**: No.

### D-10. Related issue and no dependency

- **Decision**: Name issue #4876 as a related issue. Record no dependency.
- **Alternatives**: Record #4876 as a dependency.
- **Rationale**: Issue #4876 closed through PR #4880, and its merge commit `b1360b316` is an ancestor of `main` (R-52). The uv paragraphs that this issue keeps came from that PR. Issue #4876 comment 7070815245 names this issue as the follow-up for the requirement-file text.
- **Risk**: None found.
- **Human decision**: No.

## Remote verification

Each row is one remote check. The `Result` column uses `present`, `absent`, `partial`, or `stale`. The `Line` column holds the line on `main` that the claim cites, or `0` for a file-level claim.

| ID | Claim | Path | Ref | Blob SHA | Result | Line |
|----|-------|------|-----|----------|--------|------|
| R-01 | Remote main is at commit `f03c6c9b`. | main branch | main | f03c6c9b36d612a48d7b9652998c2fd87dd777ca | present | 0 |
| R-02 | The guide exists on main. | documentation/development-setup.md | main | 1733975a7e0a0962fe5367e165a21f5831f8c3e5 | present | 0 |
| R-03 | Step 2 says the bootstrap installs the two requirement files. | documentation/development-setup.md | main | 1733975a7e0a0962fe5367e165a21f5831f8c3e5 | stale | 28 |
| R-04 | The first quoted statement of the issue, "for each present requirement file", is on main. | documentation/development-setup.md | main | 1733975a7e0a0962fe5367e165a21f5831f8c3e5 | absent | 0 |
| R-05 | The second quoted statement of the issue, the pip install used when uv is absent, is on main. | documentation/development-setup.md | main | 1733975a7e0a0962fe5367e165a21f5831f8c3e5 | absent | 0 |
| R-06 | The report paragraph says that it identifies each attempted file. | documentation/development-setup.md | main | 1733975a7e0a0962fe5367e165a21f5831f8c3e5 | stale | 83 |
| R-07 | The report paragraph says that a successful invocation reports total installation time. | documentation/development-setup.md | main | 1733975a7e0a0962fe5367e165a21f5831f8c3e5 | stale | 85 |
| R-08 | The report paragraph describes an invocation with no requirement files. | documentation/development-setup.md | main | 1733975a7e0a0962fe5367e165a21f5831f8c3e5 | stale | 86 |
| R-09 | Package sources says that the extra-source order remains unchanged. | documentation/development-setup.md | main | 1733975a7e0a0962fe5367e165a21f5831f8c3e5 | stale | 103 |
| R-10 | The settings table names UV_HTTP_RETRIES. | documentation/development-setup.md | main | 1733975a7e0a0962fe5367e165a21f5831f8c3e5 | absent | 0 |
| R-11 | The installer text names the locked sync command. | documentation/development-setup.md | main | 1733975a7e0a0962fe5367e165a21f5831f8c3e5 | absent | 0 |
| R-12 | The browser text says that the bootstrap installs the two packages of the dev extra. | documentation/development-setup.md | main | 1733975a7e0a0962fe5367e165a21f5831f8c3e5 | present | 264 |
| R-13 | The guide describes misthelper-devtools as a reviewed, immutable commit. | documentation/development-setup.md | main | 1733975a7e0a0962fe5367e165a21f5831f8c3e5 | partial | 144 |
| R-14 | The bootstrap script exists on main. | scripts/bootstrap_worktree.py | main | e16515ffa789cca7d0bdd7e9789898588e5f1312 | present | 0 |
| R-15 | The script runs `uv sync --locked --extra dev`. | scripts/bootstrap_worktree.py | main | e16515ffa789cca7d0bdd7e9789898588e5f1312 | present | 466 |
| R-16 | The script prints the report line "Installed dependencies with uv sync --locked --extra dev.". | scripts/bootstrap_worktree.py | main | e16515ffa789cca7d0bdd7e9789898588e5f1312 | present | 693 |
| R-17 | REQUIREMENT_FILES feeds only the pip export report line. | scripts/bootstrap_worktree.py | main | e16515ffa789cca7d0bdd7e9789898588e5f1312 | present | 694 |
| R-18 | The script finds uv on PATH, then in the per-user folders, then as a bootstrap module. | scripts/bootstrap_worktree.py | main | e16515ffa789cca7d0bdd7e9789898588e5f1312 | present | 302 |
| R-19 | The script installs uv with pip only when no uv is found and the Python is not externally managed. | scripts/bootstrap_worktree.py | main | e16515ffa789cca7d0bdd7e9789898588e5f1312 | present | 457 |
| R-20 | The script sets UV_LINK_MODE, UV_NATIVE_TLS, UV_SYSTEM_CERTS, UV_NO_CONFIG, UV_HTTP_RETRIES, and UV_HTTP_TIMEOUT for installer children, and removes UV_CONFIG_FILE. | scripts/bootstrap_worktree.py | main | e16515ffa789cca7d0bdd7e9789898588e5f1312 | present | 416 |
| R-21 | The script sets PIP_RETRIES and PIP_TIMEOUT for every child process. | scripts/bootstrap_worktree.py | main | e16515ffa789cca7d0bdd7e9789898588e5f1312 | present | 642 |
| R-22 | The script sets PIP_CONFIG_FILE to the null device when the public index applies. | scripts/bootstrap_worktree.py | main | e16515ffa789cca7d0bdd7e9789898588e5f1312 | present | 429 |
| R-23 | The script defines the option --public-lock-index. | scripts/bootstrap_worktree.py | main | e16515ffa789cca7d0bdd7e9789898588e5f1312 | present | 679 |
| R-24 | The script reads pip configuration once with `pip config list`. | scripts/bootstrap_worktree.py | main | e16515ffa789cca7d0bdd7e9789898588e5f1312 | present | 179 |
| R-25 | The script runs `uv lock --check` after a failed locked sync. | scripts/bootstrap_worktree.py | main | e16515ffa789cca7d0bdd7e9789898588e5f1312 | present | 497 |
| R-26 | The script runs the health check after the locked sync. | scripts/bootstrap_worktree.py | main | e16515ffa789cca7d0bdd7e9789898588e5f1312 | present | 623 |
| R-27 | The script downloads the browser in a browser child process. | scripts/bootstrap_worktree.py | main | e16515ffa789cca7d0bdd7e9789898588e5f1312 | present | 593 |
| R-28 | The script adds --use-system-ca to NODE_OPTIONS only when the option is absent. | scripts/bootstrap_worktree.py | main | e16515ffa789cca7d0bdd7e9789898588e5f1312 | present | 662 |
| R-29 | The script sets the repository credential username with `git config --local`. | scripts/bootstrap_worktree.py | main | e16515ffa789cca7d0bdd7e9789898588e5f1312 | present | 820 |
| R-30 | The script checks the active account with `gh api user`. | scripts/bootstrap_worktree.py | main | e16515ffa789cca7d0bdd7e9789898588e5f1312 | present | 848 |
| R-31 | A failed install stops the script with return code 1. | scripts/bootstrap_worktree.py | main | e16515ffa789cca7d0bdd7e9789898588e5f1312 | present | 901 |
| R-32 | The pip source parser keeps one value for each source key. | scripts/bootstrap_worktree.py | main | e16515ffa789cca7d0bdd7e9789898588e5f1312 | present | 206 |
| R-33 | The script sets UV_INDEX_URL to the public index for --public-lock-index. | scripts/bootstrap_worktree.py | main | e16515ffa789cca7d0bdd7e9789898588e5f1312 | present | 354 |
| R-34 | The STE workflow exists on main. | .github/workflows/ste-lint.yml | main | abaeff6d5e299bfa7de4dc15d04f4ef31cf13b5f | present | 0 |
| R-35 | The STE workflow grades five named files and not the guide. | .github/workflows/ste-lint.yml | main | abaeff6d5e299bfa7de4dc15d04f4ef31cf13b5f | absent | 44 |
| R-36 | The STE configuration file exists on main. | .ste-linter.toml | main | d9f28ef8faf4a4c36a4e967d5b978f96eb306253 | present | 0 |
| R-37 | AGENTS.md requires each Markdown file to score 80 or above. | AGENTS.md | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 56 |
| R-38 | The local gates table lists the STE command, and its file list does not include the guide. | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 74 |
| R-39 | The dev extra holds playwright and pytest-playwright. | pyproject.toml | main | eca34c826ea44ba4f2faefc07d04c2c117e99751 | present | 113 |
| R-40 | misthelper-devtools is pinned to a 40-character commit. | requirements-dev.txt | main | 9a528bfe03a10f7bc903f5768ef26de765bbff43 | present | 197 |
| R-41 | The changelog README allows no fragment for an internal-only change. | changelog.d/README.md | main | fcbde10e0c293390bd9df8d62a5d61f158eca384 | present | 58 |
| R-42 | The container build triggers on product paths, and its path list excludes documentation. | .github/workflows/container-build.yml | main | 737325976de75e90aa4526ab1cf2978782e648ce | present | 6 |
| R-43 | The guard test reads the guide as a policy document. | tests/guardrails/test_container_policy_docs.py | main | 1b842c302e52bcb43a95e4a2aed2366a93d94909 | present | 63 |
| R-44 | The constitution requires one changelog fragment for each change. | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 409 |
| R-45 | The constitution supersedes the practice documents when a conflict arises. | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 529 |
| R-46 | No route folder for issue 4879 exists on main. | specs/numbered/0/0/1/2/4/0/0/4 | main | no tree entry | absent | 0 |
| R-47 | The reference record spec of issue 4920 exists on main. | specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv/spec.md | main | 83b950279e45704943ad6942d23c8fc99cced492 | present | 0 |
| R-48 | The spec template exists on main. | .specify/templates/spec-template.md | main | 083ef123c7a2e56e21f3062173fb003258f927e2 | present | 0 |
| R-49 | The plan template exists on main. | .specify/templates/plan-template.md | main | 1a54553bd85cbef2178aa55efbeeb0c1942ffdde | present | 0 |
| R-50 | The tasks template exists on main. | .specify/templates/tasks-template.md | main | 7e5170324d41a6736c498d6b9fc83651f31d0778 | present | 0 |
| R-51 | The checklist template exists on main. | .specify/templates/checklist-template.md | main | 806657da09d1058823923e346a323b633114971a | present | 0 |
| R-52 | Commit b1360b316, the merge of PR 4880, is an ancestor of main. | commit b1360b316 | main | b1360b31674a3e9082c2d4103953bfc01941e786 | present | 0 |
| R-53 | No path with 4879 in its name exists on main, including no changelog fragment. | repository tree | main | no tree entry | absent | 0 |

## Local evidence

These facts come from read-only local commands. They support the remote rows. They do not count as remote checks.

- The local HEAD equals remote main at commit `f03c6c9b`.
- None of the seven open pull requests touches a target file. The target files are the guide, the bootstrap script, and the guard test. The open pull request list was read on 2026-11-26.
- Tracked files that name the guide: the guard test (line 63). Comments in the browser test (lines 29 and 30) name requirement files, not the guide.
- The guide holds semicolons only in code blocks (lines 234, 235, 289, and 361). It holds no contraction, no Latin abbreviation, and no phrasal verb from the list of words to avoid.
- The guide names no Mist endpoint. Its only Mist term is the variable `MIST_APITOKEN` (line 154).
- The script defines `REQUIREMENT_FILES` at line 59 and uses it at line 694 only.

## Sources

Local paths, read in this session:

- `AGENTS.md`, the writing style section (lines 40 to 57).
- `.github/copilot-instructions.md`, the local gates table (lines 50 to 74) and the branch rule.
- `.specify/memory/constitution.md`, the deployment steps (lines 165 to 170), the documentation section (line 409), and the governance section (line 529).
- `.specify/templates/` (spec, plan, tasks, and checklist templates).
- `documentation/quality-gates.md`, the writing gate (lines 277 to 293).
- `documentation/development-setup.md` (the whole file), and `scripts/bootstrap_worktree.py` (the whole file, 914 lines).
- `tests/guardrails/test_container_policy_docs.py` (the policy document list at lines 59 to 67).
- `changelog.d/README.md` (lines 24 to 33 and 58).
- `requirements-dev.txt` line 197, `pyproject.toml` lines 97 to 114, `.ste-linter.toml` (presence), `.github/workflows/ste-lint.yml`, and `.github/workflows/container-build.yml`.
- `specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv/` (shape only: spec, plan, tasks, analysis, design, and checklists).

Remote sources, read with `gh` in read-only mode:

- Issue #4879 (state open, label `docs`, no comments, created 2026-11-21).
- Issue #4876 (closed). Comment 7070815245 names the requirement-file text as a follow-up.
- PR #4880 (merged, merge commit `b1360b316`, changed `documentation/development-setup.md` with 10 additions and 10 deletions).
- The open pull request list (seven open, none overlapping the target files).

Upstream pages that this session fetched:

- https://docs.astral.sh/uv/reference/environment/. The page gives the default of UV_HTTP_RETRIES (3) and of UV_HTTP_TIMEOUT (30 s). It describes UV_NO_CONFIG, UV_CONFIG_FILE, UV_LINK_MODE, and UV_LOCKED. It marks UV_INDEX_URL and UV_EXTRA_INDEX_URL as deprecated. It marks UV_NATIVE_TLS as deprecated in favor of UV_SYSTEM_CERTS.
- https://pip.pypa.io/en/stable/topics/configuration/. Environment variables use the prefix PIP_ and the option name in capital letters. Setting PIP_CONFIG_FILE to os.devnull disables all configuration files.
- https://pip.pypa.io/en/stable/cli/pip/. The option --retries defaults to 5, with the variable PIP_RETRIES. The option --timeout defaults to 15 seconds, with the variable PIP_TIMEOUT.

Skills: none loaded. No listed skill covers the bootstrap script or uv.

Mist API: not applicable. The record cites no endpoint, so no OpenAPI file or coverage document was read.

Linked work: PR #3479 matched the search text "4879" in its body. Its title is a dependency bump, and it is not linked work.

## Unverified

- U-1: The current STE score of the guide, and the score of the fragment. The tool does not run in this session (brief rule 2).
- U-2: The word "reviewed" in the guide line 144. No review record was read.
- U-3: The claim "requirements.txt and pyproject.toml hold the full dependency list" (guide line 17). The two files were not compared with `uv.lock`.
- U-4: The dictionary-off mode of `ste-linter` that the CI job uses. The repository names no flag for it. The local command in the local gates table (R-38) is the only verified command.
- U-5: The purpose text that the guide gives for UV_LINK_MODE, including the OneDrive case, and for UV_NATIVE_TLS. The uv reference states the setting names and their defaults. It does not state the OneDrive case.
- U-6: Several extra index lines in pip configuration. The parser keeps one value (R-32). No run confirms the result.
- U-7: The behavior of the deprecated uv names, UV_INDEX_URL and UV_EXTRA_INDEX_URL, in the uv version that a reader installs. The repository pins no uv version for readers.
