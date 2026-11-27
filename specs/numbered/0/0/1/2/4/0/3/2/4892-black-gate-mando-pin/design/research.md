# Research: Black Gate Failure From the Mando Pin

## Summary

- The failing check is the Black (format check) job in the Quality Gates workflow. The failing step is step 5, `Run pip install -r requirements-dev.txt`. Step 6, the Black format check, is skipped.
- Pull request #4888 raises mando from 0.7.1 to 0.8.2. Radon 6.0.1 requires `mando<0.8,>=0.6`. Pip cannot satisfy both pins.
- Main keeps mando at 0.7.1. Main passes the Black job in run 45774119357.
- The fix keeps the pin, adds a Dependabot ignore rule, adds two guard tests, and adds one changelog fragment.

## Remote Verification

Each row is one remote check. The STATUS file holds the same 96 rows. Each result is `present`, `absent`, `partial`, or `stale`. Line numbers refer to the file at the stated ref. Commit and run checks use `n/a` for the blob SHA.

| ID | Claim | Path | Ref | Blob SHA | Result | Line |
| - | - | - | - | - | - | - |
| R-01 | Main pins mando 0.7.1 in requirements-dev.txt | requirements-dev.txt | main | 9a528bfe03a10f7bc903f5768ef26de765bbff43 | present | 179 |
| R-02 | PR head pins mando 0.8.2 in requirements-dev.txt | requirements-dev.txt | e86098cdc2b189d217805b3b4060ef609cbc37af | cd76ee824467ddade56342190a0d8181ee55d3d0 | present | 179 |
| R-03 | Main pins radon 6.0.1 in requirements-dev.txt | requirements-dev.txt | main | 9a528bfe03a10f7bc903f5768ef26de765bbff43 | present | 365 |
| R-04 | Main pins black 26.10.1 in requirements-dev.txt | requirements-dev.txt | main | 9a528bfe03a10f7bc903f5768ef26de765bbff43 | present | 22 |
| R-05 | requirements-dev.txt states that uv export generates it | requirements-dev.txt | main | 9a528bfe03a10f7bc903f5768ef26de765bbff43 | present | 2 |
| R-06 | Black job display name is Black (format check) | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 168 |
| R-07 | Black job installs requirements-dev.txt | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 194 |
| R-08 | Black format check step runs black --check --diff . | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 196 |
| R-09 | Workflow name is Quality Gates | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 9 |
| R-10 | Black job runs when upstream jobs fail | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 175 |
| R-11 | Dependency lock job runs uv lock --check | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 648 |
| R-12 | Dependency lock job runs the export guard | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 650 |
| R-13 | Issue sync job calls the reusable quality gate issue workflow | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 1317 |
| R-14 | Export guard compares each export with uv export output | tests/guardrails/test_dependency_export.py | main | a2a3e279dbfefb5292923d745cffa4ea4c66654d | present | 101 |
| R-15 | Lock guard checks each requirement against uv.lock | tests/guardrails/test_dependency_lock_file.py | main | 1e398e42c443073ae7df64984e3da298df345395 | present | 68 |
| R-16 | uv.lock pins mando 0.7.1 | uv.lock | main | 5445b4eb382dc9f6dd5c351ba40c521f01f93165 | present | 1301 |
| R-17 | uv.lock lists mando as a dependency of radon 6.0.1 | uv.lock | main | 5445b4eb382dc9f6dd5c351ba40c521f01f93165 | present | 2432 |
| R-18 | Dev extra pins radon 6.0.1 | pyproject.toml | main | eca34c826ea44ba4f2faefc07d04c2c117e99751 | present | 118 |
| R-19 | Runtime requirements pin mando | requirements.txt | main | 50fe63d4cf5e6071612c62c288e965190c60b969 | absent | 0 |
| R-20 | Pip entry ignores mando releases | .github/dependabot.yml | main | be5ad1ea473a41662c2d225a174daa8a6f95df84 | absent | 3 |
| R-21 | npm entry has an ignore block with a comment | .github/dependabot.yml | main | be5ad1ea473a41662c2d225a174daa8a6f95df84 | present | 45 |
| R-22 | Bandit configuration excludes tests | pyproject.toml | main | eca34c826ea44ba4f2faefc07d04c2c117e99751 | present | 503 |
| R-23 | Quality gates document lists the Black command | documentation/quality-gates.md | main | 6776d334cca5d9b43273473a06da367a65605c6d | present | 51 |
| R-24 | Repository rule says not to close update pull requests | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 533 |
| R-25 | Fragments are required for user-visible changes | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 451 |
| R-26 | Each change must add one fragment | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 409 |
| R-27 | Constitution supersedes other practice documents | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 529 |
| R-28 | Changelog README says add no fragment for an internal-only change | changelog.d/README.md | main | fcbde10e0c293390bd9df8d62a5d61f158eca384 | present | 58 |
| R-29 | Changelog guard accepts issue-number-slug names | tests/guardrails/test_changelog_fragment_policy.py | main | dbd5e8776797f12536b3bc2bd613143b85f3fc4a | present | 39 |
| R-30 | changelog.d holds 335 direct children | changelog.d | main | ece56396f47d31dfed7bebe6c69f6dda39f53d83 | present | 0 |
| R-31 | tests/guardrails holds 79 direct children | tests/guardrails | main | 17c7b7f3c0ec8acc4c4d338ea27a8eb1fa2203da | present | 0 |
| R-32 | specs/numbered/0/0/1/2 holds five children | specs/numbered/0/0/1/2 | main | 6fe73b539f8c9f60287ac92b27ae521e59c73503 | present | 0 |
| R-33 | specs/numbered/0/0/1/2/4 holds children 1 and 2 | specs/numbered/0/0/1/2/4 | main | 1be0cb847d4cf5623c455aaaf39274896d25dc1d | present | 0 |
| R-34 | Route folder for issue 4892 is absent | specs/numbered/0/0/1/2/4/0/3/2 | main | none, path absent | absent | 0 |
| R-35 | No record folder for issue 4892 exists under specs | specs | main | none, no match | absent | 0 |
| R-36 | Record 4867 keeps mando 0.7.1 and states the radon range | specs/numbered/0/0/1/2/3/4/3/2/4867-refresh-dependencies/design/research.md | main | 36273c6c217a3a8e92643323bfe7feb7f5886d60 | present | 71 |
| R-37 | Spec route base is five | .specify/scripts/powershell/spec-route.ps1 | main | 37293a255f9b5de20ccb2b3ef0ad15717bab2826 | present | 17 |
| R-38 | Numeric route guard test exists | tests/guardrails/test_spec_route_contract.py | main | b174399ad5f23f4844dc442954bf203be07342f3 | present | 464 |
| R-39 | Five-children guard test exists | tests/guardrails/test_process_folder_structure.py | main | f3b3f7f6853ff8652e44455f54e88cfd4d12b1f5 | present | 133 |
| R-40 | Spec template exists | .specify/templates/spec-template.md | main | 083ef123c7a2e56e21f3062173fb003258f927e2 | present | 1 |
| R-41 | Plan template exists | .specify/templates/plan-template.md | main | 1a54553bd85cbef2178aa55efbeeb0c1942ffdde | present | 1 |
| R-42 | Tasks template exists | .specify/templates/tasks-template.md | main | 7e5170324d41a6736c498d6b9fc83651f31d0778 | present | 1 |
| R-43 | Checklist template exists | .specify/templates/checklist-template.md | main | 806657da09d1058823923e346a323b633114971a | present | 1 |
| R-44 | Reference record 4920 has a spec file | specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv/spec.md | main | 83b950279e45704943ad6942d23c8fc99cced492 | present | 1 |
| R-45 | Dependabot schema defines versions as the package manager pattern | src/schemas/json/dependabot-2.0.json in SchemaStore/schemastore | master | c37db1f4f01e54b5bfbd08571eaa5c386a30e917 | present | 1036 |
| R-46 | Radon 6.0.1 requires mando (<0.8,>=0.6) | https://pypi.org/pypi/radon/6.0.1/json | PyPI release 6.0.1 | n/a upstream | present | 0 |
| R-47 | Radon 6.0.1 is the latest release on the PyPI project page | https://pypi.org/project/radon/#history | PyPI project page | n/a upstream | present | 0 |
| R-48 | Commit 5bb4b385 exists and merges the pull request head into its base | commit 5bb4b385a2e9c5e7d0e886e04a1c3d03989b9f71 | commit | n/a commit check | present | 0 |
| R-49 | Commit e86098cd exists and is the pull request head | commit e86098cdc2b189d217805b3b4060ef609cbc37af | commit | n/a commit check | present | 0 |
| R-50 | Main tip is f03c6c9b and matches the local HEAD | heads/main | main | f03c6c9b36d612a48d7b9652998c2fd87dd777ca | present | 0 |
| R-51 | Pull request #4888 is open, has head branch dependabot/pip/mando-0.8.2, and changes requirements-dev.txt only | requirements-dev.txt in pull request #4888 | e86098cdc2b189d217805b3b4060ef609cbc37af | cd76ee824467ddade56342190a0d8181ee55d3d0 | present | 0 |
| R-52 | Job 137339161296 fails at step 5 and skips step 6 | job 137339161296 of run 45064243269 | e86098cdc2b189d217805b3b4060ef609cbc37af | n/a CI log | present | 0 |
| R-53 | CI log holds the resolver conflict for mando 0.8.2 | job 137339161296 CI log | e86098cdc2b189d217805b3b4060ef609cbc37af | n/a CI log | present | 585 |
| R-54 | CI log holds ResolutionImpossible | job 137339161296 CI log | e86098cdc2b189d217805b3b4060ef609cbc37af | n/a CI log | present | 598 |
| R-55 | Twenty-six of 28 failed jobs hold the same conflict | run 45064243269 jobs | e86098cdc2b189d217805b3b4060ef609cbc37af | n/a CI logs | present | 0 |
| R-56 | Black job passes on main in run 45774119357 | job 139759629310 of run 45774119357 | main | n/a CI log | present | 0 |
| R-57 | All 33 jobs pass on main in run 45774119357 | run 45774119357 | main | n/a CI logs | present | 0 |
| R-58 | Fourteen sibling gate issues are open | issues 4891 and 4893 to 4905 | n/a | n/a GitHub issues | present | 0 |
| R-59 | Issue 4867 is closed and pull request 4871 is merged | issue 4867 and pull request 4871 | n/a | n/a GitHub | present | 0 |
| R-60 | No pull request links issue 4892 | pull request search for 4892 | n/a | n/a GitHub search | absent | 0 |
| R-61 | Label in-progress exists | repository labels | n/a | n/a GitHub labels | present | 0 |
| R-62 | Five documentation files state no Dependabot, mando, or radon policy | documentation/architecture.md, development-setup.md, container-deployment.md, operator-guide.md, quality-gates.md | main | n/a five files | absent | 0 |
| R-63 | Local gates table Format row runs python -m black --check . | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 59 |
| R-64 | Local gates table Tests row runs the changed test file | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 61 |
| R-65 | Local gates table STE row runs ste-linter with minimum score 80 | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 74 |
| R-66 | Local gates table Security lint row runs bandit with the pyproject configuration | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 67 |
| R-67 | Local gates table Symbols row runs symbol-diff | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 73 |
| R-68 | Required check after the local commit runs test-quality-analyzer | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 124 |
| R-69 | Second pytest-chunks command covers tests/guardrails | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 88 |
| R-70 | Local gates table Lint row runs python -m ruff check . | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 58 |
| R-71 | Local gates table Compile row runs py_compile on MistHelper.py | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 57 |
| R-72 | Local gates table Coverage row runs the coverage command | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 64 |
| R-73 | Local gates table Types row runs mypy with MYPY_PATHS | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 60 |
| R-74 | Local gates table Complexity row runs radon with complexity-gate | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 66 |
| R-75 | Local gates table rows from line 68 list the remaining gates | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 68 |
| R-76 | CI MYPY_PATHS lists product paths only | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 93 |
| R-77 | CI RADON_PATHS lists one test file, not the guardrails module | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 99 |
| R-78 | CI VULTURE_PATHS lists product paths only | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 101 |
| R-79 | CI PYDOCSTYLE_PATHS lists product paths only | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 104 |
| R-80 | CI INTERROGATE_PATHS lists product paths only | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 107 |
| R-81 | Ruff job runs on ubuntu-latest | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 142 |
| R-82 | pyproject requires Python 3.15 or newer | pyproject.toml | main | eca34c826ea44ba4f2faefc07d04c2c117e99751 | present | 23 |
| R-83 | PyYAML is pinned at 6.0.4 | requirements-dev.txt | main | 9a528bfe03a10f7bc903f5768ef26de765bbff43 | present | 356 |
| R-84 | packaging is pinned at 26.3 | requirements-dev.txt | main | 9a528bfe03a10f7bc903f5768ef26de765bbff43 | present | 228 |
| R-85 | Lock guard module resolves paths with pathlib | tests/guardrails/test_dependency_lock_file.py | main | 1e398e42c443073ae7df64984e3da298df345395 | present | 22 |
| R-86 | Lock guard module holds eight top-level names before the change | tests/guardrails/test_dependency_lock_file.py | main | 1e398e42c443073ae7df64984e3da298df345395 | present | 20 |
| R-87 | Container build runs for product file changes | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 473 |
| R-88 | Bandit job runs bandit with the pyproject configuration over the repository | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 451 |
| R-89 | Coverage shards job exists | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 242 |
| R-90 | An issue in progress carries in-progress | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 433 |
| R-91 | Constitution requires a status label when in progress | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 494 |
| R-92 | AGENTS forbids removing a gate | AGENTS.md | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 308 |
| R-93 | AGENTS requires a contract test for each workflow value a future edit can remove | AGENTS.md | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 310 |
| R-94 | Constitution requires py_compile of MistHelper.py before each commit | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 370 |
| R-95 | Constitution version is 1.9.0 | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 562 |
| R-96 | Issue 4892 carries labels bug, ci, and quality-gate | GitHub issue 4892 | n/a | n/a GitHub | present | 0 |

## Decisions

### D-1. Classify the failure as a pip resolver conflict

- **Decision**: The failing check is the Black (format check) job. The failing step is step 5. The Black format check never runs.
- **Alternatives**: (a) A format defect in the pull request. (b) A runner or network fault. (c) A resolver conflict in `requirements-dev.txt`.
- **Chosen**: (c).
- **Reason**: Step 6 is skipped (R-52). The log names the conflict and `ResolutionImpossible` (R-53, R-54). Main passes the same job (R-56). Pull request #4888 changes mando only (R-51).
- **Risk**: Low. A real format defect stays hidden until pip succeeds. The local Format gate covers it.
- **Human decision required**: No.

### D-2. Keep the mando pin at 0.7.1

- **Decision**: Mando stays at 0.7.1 in `uv.lock` and `requirements-dev.txt`.
- **Alternatives**: (a) Keep 0.7.1 and ignore mando 0.8 and later. (b) Upgrade radon to a release that accepts mando 0.8. (c) Merge the bump and remove radon. (d) Remove the mando line from `requirements-dev.txt`.
- **Chosen**: (a).
- **Reason**: Radon 6.0.1 is the latest release (R-47). Its metadata requires `<0.8,>=0.6` (R-46). No radon release accepts mando 0.8, so option (b) is not available. Option (c) replaces the complexity gate, which is out of scope. Option (d) changes nothing, because uv still adds mando 0.7.1 through radon (R-17).
- **Risk**: Dependabot can propose mando 0.8 again. Decision D-3 mitigates that risk.
- **Human decision required**: No.

### D-3. Add a Dependabot ignore rule for mando 0.8 and later

- **Decision**: The pip entry gains an `ignore` list with `dependency-name: "mando"` and `versions: [">=0.8"]`.
- **Alternatives**: (a) Ignore the version range `>=0.8`. (b) Ignore by `update-types`. (c) Ignore every mando update. (d) Make no configuration change.
- **Chosen**: (a).
- **Reason**: The schema says a range uses the package manager pattern (R-45). The npm entry already uses an ignore block with comments (R-21). Option (b) depends on how Dependabot classifies 0.x releases, and the schema does not state that. Option (c) also hides releases that radon accepts. Option (d) lets the same bump return.
- **Risk**: Runtime acceptance is unverified (U-1). The rule must be removed when radon accepts a newer mando.
- **Human decision required**: No.

### D-4. Keep pull request #4888 open and unmerged

- **Decision**: This change does not merge or close pull request #4888.
- **Alternatives**: (a) Keep it open and unmerged. (b) Close it now. (c) Merge it. (d) Push a fix to its branch.
- **Chosen**: (a).
- **Reason**: The repository rule says not to close update pull requests (R-24). Merging stops the install in each job that installs `requirements-dev.txt` (R-52, R-53). Dependabot manages that branch, so a manual push is not part of this change.
- **Risk**: The red checks and the fourteen sibling issues stay open until the owner acts (U-5).
- **Human decision required**: No.

### D-5. Keep requirements-dev.txt and uv.lock unchanged

- **Decision**: This change edits neither file. It does not hand edit the export.
- **Alternatives**: (a) Leave both unchanged. (b) Hand edit `requirements-dev.txt` to mando 0.8.2. (c) Run `uv lock` with the bump.
- **Chosen**: (a).
- **Reason**: The file header states that uv generates it (R-05). The export guard compares it with `uv export` (R-14). The lock guard checks it against `uv.lock` (R-15). Option (c) cannot pass, because radon forbids mando 0.8 (R-46).
- **Risk**: None for this change.
- **Human decision required**: No.

### D-6. Add two guard tests to the existing lock file test module

- **Decision**: Add class `DependabotPolicy` and two test functions to `tests\guardrails\test_dependency_lock_file.py`.
- **Alternatives**: (a) Add to the existing module. (b) Add a new module in `tests\guardrails\`. (c) Add no test.
- **Chosen**: (a).
- **Reason**: The module guards dependency declarations (R-15). The guardrails folder holds 79 children (R-31), and the constitution forbids a new direct child in a noncompliant parent. `AGENTS.md` requires a contract test for each value that a future edit can remove (R-93).
- **Risk**: The module holds 11 top-level names after the change. The debt is recorded in `plan.md`, Complexity Tracking.
- **Human decision required**: No.

### D-7. Add one changelog fragment

- **Decision**: Add `changelog.d\issue-4892-black-gate-mando-pin.md`.
- **Alternatives**: (a) Add the fragment. (b) Add no fragment under the README rule.
- **Chosen**: (a).
- **Reason**: The constitution requires one fragment for each change (R-26). The constitution governs when rules conflict (R-27). The README says to add no fragment for an internal-only change (R-28). The copilot instructions require one only for user-visible changes (R-25).
- **Risk**: The owner must reconcile the rules (analysis U-b).
- **Human decision required**: No.

### D-8. Change no workflow, Black configuration, or product code

- **Decision**: `.github\workflows\ci.yml`, `pyproject.toml`, and product files stay unchanged.
- **Alternatives**: (a) Run black before the pip install. (b) Remove the Black job from the install path. (c) Reformat files.
- **Chosen**: None of them.
- **Reason**: The Black job needs its install, so black cannot run before pip (R-07, R-08). `AGENTS.md` forbids removing a gate (R-92). Main passes the Black job (R-56), so no file needs reformatting.
- **Risk**: None.
- **Human decision required**: No.

### D-9. Add no documentation file

- **Decision**: The policy lives in the comment block of `.github\dependabot.yml`.
- **Alternatives**: (a) Keep the comment block. (b) Add a section to `documentation\quality-gates.md`.
- **Chosen**: (a).
- **Reason**: The npm entry uses the same pattern (R-21). Five documentation files hold no Dependabot, mando, or radon policy (R-62). `AGENTS.md` asks for one fact in one location.
- **Risk**: A reader must open the configuration file to see the policy.
- **Human decision required**: No.

### D-10. Use the branch and commit names

- **Decision**: Branch `fix/4892-black-gate-mando-pin`. Commit subject and pull request title `fix(ci): ignore mando releases that radon 6.0.1 rejects`.
- **Alternatives**: (a) A `chore` branch. (b) A title that names only the Black job.
- **Chosen**: The `fix` branch and the chosen title.
- **Reason**: The change repairs a failing gate, and the issue carries the `bug` label (R-96). The title names the cause, so a reviewer finds the reason at once.
- **Risk**: None.
- **Human decision required**: No.

### D-11. Add the in-progress label only

- **Decision**: Add label `in-progress` to issue #4892. Keep `bug` and `ci`.
- **Alternatives**: (a) Add `chore` or `dependencies`. (b) Add no label.
- **Chosen**: Add `in-progress` only.
- **Reason**: The constitution requires a status label for work in progress (R-91). The label exists (R-61). The issue already holds a type label and a scope label (R-96).
- **Risk**: None.
- **Human decision required**: No.

### D-12. Use route folder 4892-black-gate-mando-pin and size S

- **Decision**: The record folder is `specs\numbered\0\0\1\2\4\0\3\2\4892-black-gate-mando-pin`. The size is S.
- **Alternatives**: (a) A broader slug such as `black-gate-failure`. (b) Size M.
- **Chosen**: The chosen slug and size S.
- **Reason**: The route digits match the base-5 value of 4892 (R-37). The slug names the pin and the gate. The change touches one configuration file, one test module, one fragment, and one record folder. It changes no runtime behavior.
- **Risk**: None.
- **Human decision required**: No.

## Sources

- S-1. Local working tree at `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper`. HEAD is f03c6c9b36d612a48d7b9652998c2fd87dd777ca (R-50). Git commands were read-only.
- S-2. GitHub REST API through `gh api`, and `gh` read commands for runs, jobs, pull requests, issues, and labels. GET requests only.
- S-3. CI log of job 137339161296 through `gh run view --job 137339161296 --log-failed` (R-53, R-54).
- S-4. https://pypi.org/pypi/radon/6.0.1/json, fetched with the web fetch tool (R-46).
- S-5. https://pypi.org/project/radon/#history, fetched with the web fetch tool (R-47).
- S-6. SchemaStore `src/schemas/json/dependabot-2.0.json`, read through `gh api repos/SchemaStore/schemastore/contents/src/schemas/json/dependabot-2.0.json` (R-45). Human URL: https://github.com/SchemaStore/schemastore/blob/master/src/schemas/json/dependabot-2.0.json
- S-7. Spec Kit templates in `.specify\templates\` (R-40 to R-43).
- S-8. Reference record `specs\numbered\0\0\1\2\4\1\4\0\4920-ex-hardware-inventory-csv\` (R-44). The shape was copied. The content was not copied.
- S-9. Blocked and not used: the Dependabot option pages on docs.github.com. The tool returned WebFetchBlockedUrlError for address 100.64.1.91.
- S-10. Skill tool: no skill loaded. This issue has no Podman or Juniper device question.

## Unverified

- U-1. Dependabot accepts `versions: [">=0.8"]` at runtime. Reason: the docs.github.com pages are blocked (S-9). Only the SchemaStore schema was read (R-45).
- U-2. Dependabot closes pull request #4888 after this change merges. Reason: the same docs pages are blocked (S-9). The owner checks the pull request page.
- U-3. The two new guard tests pass or fail as planned. Reason: this session runs no test, as rule 2 requires.
- U-4. The lock guard and the export guard fail on the pull request #4888 head after pip succeeds. Reason: job 137339161296 stopped at step 5 (R-52). The result follows from R-15 and R-16 by reading the code.
- U-5. The fourteen sibling issues close when pull request #4888 closes. Reason: the reusable workflow in `jmorrison-juniper/misthelper-devtools` was not read.
- U-6. The ste-linter scores of the new files. Reason: rule 2 prohibits a linter run in this session.
- U-7. Black passes on the fix branch. Reason: rule 2 prohibits a formatter run. Evidence exists for main only (R-56).
- U-8. The counts in R-30 and R-31 still hold at merge time. Reason: each count comes from one tree snapshot taken at check time.
