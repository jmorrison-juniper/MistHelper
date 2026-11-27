# Research: Netcool Runbook Smoke Package Conformance

**Issue**: #4945. **Route**: `specs/numbered/0/0/1/2/4/2/4/0`. **Record**: `4945-netcool-runbook-smoke-conformance`.

## Method

1. Read the issue body with `gh issue view 4945 -R jmorrison-juniper/MistHelper`. The issue has no comments. It was created at 2026-11-26T06:56:14Z and updated at 06:58:41Z. Its labels are `refactor`, `tests`, and `in-progress`.
2. Ran `gh pr list -R jmorrison-juniper/MistHelper --state all --search "4945"`. The result is an empty list. No pull request links to the issue.
3. Read the issues that the body names. Issue #4937 is closed. Its closing decision accepts the written Complexity Tracking exception and amends nothing. Issue #4944 is open and tracks the folder debt. Issue #4934 is the feature issue. Its record exists on `main` (row R71).
4. Searched `specs\` in the working tree for a folder whose name starts with `4945-`. None exists. The route `specs/numbered/0/0/1/2/4/2/4/0` is absent on `main` (rows R72 and R73).
5. Fetched the full remote tree of `main` in one call (`gh api repos/jmorrison-juniper/MistHelper/git/trees/main?recursive=1`). The tree holds 11,404 entries and is not truncated. The tree filter ran in PowerShell, which avoids quoting problems with a `--jq` expression.
6. Read the OpenAPI YAML from the local tree. The YAML is large, so its lines come from the local file. A local line is valid when the local index blob equals the remote blob (method item 7). The local index blob `b7fc2bfb` equals the remote blob SHA from the contents API (row R64). The JSON twin, which is the package default, has the remote blob `5f9f4ce9` (row R67). Its content was not read.
7. Compared the local index blob (`git -C <repo> ls-files -s`) with the remote blob for each package, test, and CI file. All eleven package files, all five test files, `ci.yml`, `pyproject.toml`, the constitution, `AGENTS.md`, and the copilot instructions have equal blob SHAs.
8. Read the local SDK in `.venv\Lib\site-packages\mistapi`. The SDK is not repository code, so it has no remote row.
9. Read the local `misthelper_devtools` package (`.venv\Lib\site-packages\misthelper_devtools`) for the advisory task audit rules. The gate executables are present in `.venv\Scripts`.
10. No build, test, lint, format, install, container, or repository script ran. All repository reads used `view`, `grep`, `glob`, PowerShell read commands, and `gh` reads.

**Skill tool**: Not used. The issue asks no Podman, container, or Juniper device question, and no local skill matches the package work.

**Deferred tools**: A tool search found two jPyTest and GTest context tools. Neither applies, because this record writes no tests and the repository test conventions govern the design.

## Structure measurements

Measured on `main` blobs. The function measures use a line-based reader over the same content. Each measure follows the decision in the table below.

| Measure | Result |
| - | - |
| Functions examined in the package, including nested functions | 189 |
| Functions that break a code-line limit without docstrings | 4 (`filter_verdict`, `first_site`, `_judge`, `_attempt`) |
| Functions that break a code-line limit with docstrings | 43 |
| Functions that break the statement limit of five per block | 14 |
| Functions that break the union of the two rules, without docstrings | 14 (the issue's list) |
| Functions that break the parameter limit | 0 |
| Functions that break the body-block limit | 0 |
| Classes examined | 45 |
| Classes that break the method limit of five | 0 |
| Modules with six top-level names when the logger counts | 8 |
| Modules with five or fewer top-level names when the logger does not count | 11 |
| Package children, repository convention | Root 5, `checks/` 5 |
| Package children, all files including `__init__.py` | Root 6, `checks/` 6 |

## Decisions

Each decision names the alternatives, the choice, the reason, and the risk. No decision needs a human (section 6 of the brief). Categories of section 6 do not apply: no licensing text, no destruction of production data, no credential policy, and no product priority changes.

**D-1 Code-line measure.** Alternatives: (a) count every physical line of the function, including docstrings and comments. (b) count code lines, excluding blank, comment-only, and docstring lines. Choice: (b). Reason: the issue says "25 code lines". Measure (b) produces exactly the issue's function list when combined with D-2. Risk: a reader who uses the physical count finds 43 functions. Analysis A-01 records this risk.

**D-2 Block and statement measure.** Alternatives: (a) count the docstring as a statement. (b) exclude the docstring, and do not count the clause keywords `elif`, `else`, `except`, and `finally` as statements. Each clause body is one block. Choice: (b). Reason: the issue's list matches (b). The guard test TEST-01 defines the measure in code. Risk: a different tool counts differently. The guard fixes the rule for this package.

**D-3 Module name measure.** Alternatives: (a) count the module logger. (b) exclude the lower-case logger, because only upper-case names read as constants. Choice: (a), the stricter reading. The target layout passes both readings. Risk: none for the target. The current state breaks the strict reading in eight modules (analysis A-02).

**D-4 Directory measure.** Alternatives: (a) count `__init__.py`. (b) exclude `__init__.py`, as the repository convention does. Choice: (b). Reason: the existing nested guard counts modules with `name != "__init__.py"` (`tests/guardrails/test_nested_package_structure.py` line 119, row R55). The copilot instructions state the same convention (row R40). Risk: a reader who counts `__init__.py` finds six children at the package root and in `checks/`. The target layout has five children in each of those directories under the convention. Analysis A-02 records the risk.

**D-5 Class member measure.** Alternatives: (a) count methods only. (b) count methods, fields, and enum members. Choice: (a). Reason: the issue says "five methods in a class". `CallRecord.ErrorClass` holds ten enum members that cannot split. Risk: a reader who counts fields finds `CallGovernor` with ten fields. The rule applies to methods only.

**D-6 Target layout.** Alternatives: (a) keep the flat modules and add helper modules. (b) one new sub-package for all helpers. Choice: the layout in `plan.md`, with seven new sub-package directories. Reason: flat modules break the five-name limit, and one sub-package breaks the five-child limit. Risk: many moved files. The change map in `plan.md` lists each one.

**D-7 Import path changes.** Alternatives: (a) keep old modules as re-export shims. (b) change each import path in the same change and delete old modules. Choice: (b). Reason: the issue requires it. AGENTS.md, section Code quality, Structure, says "Do not add or keep a compatibility shim". Risk: each call site and each test changes. TEST-10 and the old-path search catch a missed import.

**D-8 Entry point and `RunReport` placement.** Alternatives: (a) keep `RunReport` in a reporting module. (b) move `RunReport` into `__main__.py`. Choice: (b). Reason: `RunReport` reads check types. The reporting layer must not import the checks layer (plan dependency rule). The entry point name stays (rows R02 and R48).

**D-9 Structure guard location.** Alternatives: (a) a new file under `tests/guardrails/`, which holds 79 children (remote tree). (b) a new file under `tests/unit/scripts/netcool_runbook_smoke/`, which would hold six children. (c) extend the existing `tests/guardrails/test_nested_package_structure.py`. Choice: (c). Reason: the constitution forbids a new direct child of a noncompliant parent. The existing file already counts child directories. Risk: the file grows. The structure scanner adds a package root scan beside the `src` ratchet.

**D-10 Gate guard location.** Alternatives: (a) a new file under `tests/guardrails/`. (b) extend `tests/guardrails/test_ci_gate_triggers.py`. Choice: (b). Reason: the file already loads `ci.yml` with `yaml` (row R51, function `_parse` at line 58) from the path that row R50 names (line 35). Risk: none beyond the file growth.

**D-11 Unit test location.** Alternatives: (a) new test modules. (b) add tests to the five existing modules by subject. Choice: (b). Reason: the folder holds five children (remote tree). The test-quality baseline keys on file paths, so moving files creates new findings. Risk: the five modules grow.

**D-12 CI gate design.** Alternatives: (a) remove `scripts` from the three exclusions. (b) add the package path to the variables and add explicit steps with counts. Choice: (b). Reason: option (a) would send all other scripts into the gates and create many findings. The explicit steps keep the exclusions. No new job is added. `pyproject.toml` does not change. Risk: Ruff or Bandit may skip an explicit path. The count step and TEST-08 cover that risk.

**D-13 mypy strict and override policy.** Alternatives: (a) add the package to `MYPY_PATHS` with a relaxing `[[tool.mypy.overrides]]` section, as the openai script packages do (`pyproject.toml` lines 387 to 416, row R30). (b) add the package `__init__.py` to `MYPY_PATHS`, keep strict settings, and fix each error. Choice: (b). Reason: the constitution forbids a suppression shortcut, and a relaxing override is one. The precedent for an explicit `__init__.py` path is the current `MYPY_PATHS` value (`ci.yml` line 93, row R18). Risk: mypy may report many errors. T004 measures them first.

**D-14 Coverage.** Alternatives: (a) add the package to the CI coverage step. (b) measure the package locally and record the value. Choice: (b). Reason: the CI coverage step measures `SRC_PATH` only (row R25, line 311). The issue asks for 95 percent for the package, not a CI gate. Risk: a later change can reduce coverage without a gate. The pull request records the value.

**D-15 Test count.** Alternatives: (a) accept the issue's figure of 227. (b) measure the collected count before and after the change and require equality. Choice: (b). Reason: a static count of `def test_` gives 194 (14, 58, 44, 36, and 42 in rows R12 to R16). The issue's figure could include parameter expansions. Twelve `parametrize` decorators exist. Risk: the collected count differs from both figures. T003 records the actual value.

**D-16 Changelog fragment.** Alternatives: (a) no fragment, because the change is internal (`changelog.d/README.md` line 58, row R45). (b) add one fragment (constitution Documentation section: "Each change MUST add one unique fragment"). Choice: (b). Reason: the constitution outranks the README. The constitution says it supersedes other practice documents. The file name follows the README table for an open issue, `issue-<number>-<slug>.md` (row R46 shows the precedent). The name stays after the pull request opens. Risk: a reviewer may read the README literally. The pull request body states the constitution rule.

**D-17 Branch, commit, and title.** Alternatives: (a) branch `refactor/4945-netcool-runbook-smoke-conformance`. (b) branch `chore/4945-netcool-runbook-smoke-conformance`. Choice: (b). Reason: AGENTS.md section "Branch" allows the types `feat`, `fix`, `chore`, and `docs`. The commit type is `refactor`, which AGENTS.md allows. The pull request title uses the form `type(scope): description` (constitution Principle IV, step 4). Commit and title: `refactor(netcool-smoke): conform the package to the constitution and CI gates`.

**D-18 Labels.** Choice: no change. The issue already carries `refactor`, `tests`, and `in-progress`. The copilot instructions allow one scope label. Adding `ci` would make two scope labels.

**D-19 Size.** Choice: `L`. Reason: about 37 package files, 5 test modules, two guard files, one workflow file, and one changelog fragment. The work splits into parallel tasks (T021 to T025). `M` understates the change. `XL` overstates it, because no multi-week sequence exists.

**D-20 Mist transport.** Choice: no owned transport. The package calls `APISession.mist_get` (row R98). The SDK method is defined at `.venv\Lib\site-packages\mistapi\__api_request.py` line 260, and `APISession` is defined at `.venv\Lib\site-packages\mistapi\__api_session.py` line 52. The SDK pin `mistapi>=0.64.0,<0.65` allows the installed version 0.64.1 (`.venv\Lib\site-packages\mistapi-0.64.1.dist-info`). The owned-transport contract tests do not apply.

**D-21 Data paths and container.** Choice: evidence stays under `test-artifacts/` (row R102). No product output goes to `data/`. The `Dockerfile` COPY sources hold no repository `scripts` folder (row R69), so the image contents do not change.

**D-22 Principle IV step 12.** Choice: step 12 (deploy and check health) does not apply, because the image contents do not change (row R69). Steps 10 and 11 still run in `T-MERGE`. Reason: the constitution says no step may be skipped, so the record states this exception in `plan.md`. Risk: an operator reads the exception as a skipped step. The pull request body states the reason.

**D-23 Comment rule.** Alternatives: (a) a comment on every physical line. (b) a comment on the first physical line of each statement, with continuation lines exempt. Choice: (b). Reason: constitution Principle VI exempts closing braces, parentheses, and decorators. A continuation line of a multi-line statement carries no separate action. TEST-05 uses `tokenize` to find the first line of each statement and check for a comment.

**D-24 Comment sample audit.** Choice: draw 40 comment lines at random from the package with seed 4945. A line passes when its comment states a cause and a purpose. The threshold is 36 passing lines, from the issue. The sampling procedure is in `design/quickstart.md`.

**D-25 Helper placement.** Choice: each new helper is a method of a class that has room for it, or of a new class in the same sub-package. No standalone helper function is added. Reason: AGENTS.md "Put behavior in a class" and constitution Principle II.

**D-26 Human decisions.** Choice: none. Every decision above is within the authority of the record. The owner delegated the issue decisions on 2026-11-26.

## Remote verification table

Each row records one check on `main`. Result values: `present` means the claim holds on `main`. `absent` means the named path or text is missing on `main`. `partial` and `stale` do not occur. The ref is `main` for every row. Line 0 means a path-level check.

| ID | Claim | Path | Blob SHA | Result | Line |
| - | - | - | - | - | - |
| R01 | Package initializer exists | scripts/netcool_runbook_smoke/__init__.py | 359b4334e2700da266f017c8b0acdf803b664859 | present | 0 |
| R02 | Package entry point exists | scripts/netcool_runbook_smoke/__main__.py | 9762671c48a4767c8a64f8764eefcfef12643a44 | present | 0 |
| R03 | Client module exists | scripts/netcool_runbook_smoke/client.py | da54b0c22449362ff84a8e2766b2942037283c26 | present | 0 |
| R04 | Command module exists | scripts/netcool_runbook_smoke/command.py | 6d12bd8fd9b9f19bdbd6dc8701773dea327debbf | present | 0 |
| R05 | Documents module exists | scripts/netcool_runbook_smoke/documents.py | ce21576501a683dd4b115ddc06488b1eba4e345e | present | 0 |
| R06 | Checks initializer exists | scripts/netcool_runbook_smoke/checks/__init__.py | 2079ae9db2bf49182397116e6d463a5e1762b997 | present | 0 |
| R07 | Catalog checks module exists | scripts/netcool_runbook_smoke/checks/catalogs.py | 9b3a94c197cb14cd533ac30df1fae04df74237cb | present | 0 |
| R08 | Identity checks module exists | scripts/netcool_runbook_smoke/checks/identity.py | 91fdd0d744dc0b480d0ccba5c61d723887e00082 | present | 0 |
| R09 | Scope checks module exists | scripts/netcool_runbook_smoke/checks/scope.py | bbf00175418cac91b8bea656173a37624b77a8dd | present | 0 |
| R10 | Search checks module exists | scripts/netcool_runbook_smoke/checks/searches.py | 9d9a28dbb08b4c73645f0cd3e7ced8eac68e08ef | present | 0 |
| R11 | Support module exists | scripts/netcool_runbook_smoke/checks/support.py | d14a4ac42d3717ece9af28d17997a3d6e83e376a | present | 0 |
| R12 | Runbook document test module exists, 14 test functions | tests/unit/scripts/netcool_runbook_smoke/test_netcool_runbook_document.py | 223e4915be7f9e6e1a351ace89bbd0d8b79bf693 | present | 0 |
| R13 | Check test module exists, 58 test functions | tests/unit/scripts/netcool_runbook_smoke/test_netcool_smoke_checks.py | e3a4cca9a753a66e27c997385f5ffef522c012c7 | present | 0 |
| R14 | Client test module exists, 44 test functions | tests/unit/scripts/netcool_runbook_smoke/test_netcool_smoke_client.py | 6ff9f726d86c87bfd798dbf1646620e5d7fcc8f8 | present | 0 |
| R15 | Command test module exists, 36 test functions | tests/unit/scripts/netcool_runbook_smoke/test_netcool_smoke_command.py | af6580ab0478c101abc436daee7743995dc14645 | present | 0 |
| R16 | Document test module exists, 42 test functions | tests/unit/scripts/netcool_runbook_smoke/test_netcool_smoke_documents.py | a586fef14c95903710b0e39f919ce906a854211d | present | 0 |
| R17 | CI workflow exists | .github/workflows/ci.yml | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 0 |
| R18 | MYPY_PATHS names two script initializers and no path under the package | .github/workflows/ci.yml | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | absent | 93 |
| R19 | RADON_PATHS names no path under the package | .github/workflows/ci.yml | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | absent | 99 |
| R20 | VULTURE_PATHS names no path under the package | .github/workflows/ci.yml | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | absent | 101 |
| R21 | PYDOCSTYLE_PATHS names no path under the package | .github/workflows/ci.yml | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | absent | 104 |
| R22 | INTERROGATE_PATHS names no path under the package | .github/workflows/ci.yml | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | absent | 107 |
| R23 | Ruff job runs `ruff check .` | .github/workflows/ci.yml | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 165 |
| R24 | Bandit job runs `bandit -c pyproject.toml -r .` | .github/workflows/ci.yml | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 451 |
| R25 | Coverage step measures `SRC_PATH` only | .github/workflows/ci.yml | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 311 |
| R26 | pyproject.toml exists | pyproject.toml | eca34c826ea44ba4f2faefc07d04c2c117e99751 | present | 0 |
| R27 | Ruff `extend-exclude` names `scripts` | pyproject.toml | eca34c826ea44ba4f2faefc07d04c2c117e99751 | present | 206 |
| R28 | Mypy `exclude` names `scripts` | pyproject.toml | eca34c826ea44ba4f2faefc07d04c2c117e99751 | present | 324 |
| R29 | Bandit `exclude_dirs` names `scripts` | pyproject.toml | eca34c826ea44ba4f2faefc07d04c2c117e99751 | present | 506 |
| R30 | Mypy override names the openai script packages | pyproject.toml | eca34c826ea44ba4f2faefc07d04c2c117e99751 | present | 387 |
| R31 | Constitution file exists | .specify/memory/constitution.md | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 0 |
| R32 | Principle I heading exists | .specify/memory/constitution.md | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 38 |
| R33 | Principle VI heading exists | .specify/memory/constitution.md | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 204 |
| R34 | Principle VII heading exists | .specify/memory/constitution.md | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 235 |
| R35 | Governance heading exists | .specify/memory/constitution.md | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 526 |
| R36 | Complexity Tracking table requirement exists | .specify/memory/constitution.md | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 548 |
| R37 | AGENTS.md exists | AGENTS.md | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 0 |
| R38 | Copilot instructions exist | .github/copilot-instructions.md | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 0 |
| R39 | Copilot instructions name the Mist API JSON specification | .github/copilot-instructions.md | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 597 |
| R40 | Copilot instructions state the child-count convention without `__init__.py` | .github/copilot-instructions.md | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 259 |
| R41 | Quality gates document exists | documentation/quality-gates.md | 6776d334cca5d9b43273473a06da367a65605c6d | present | 0 |
| R42 | CI installs `requirements-dev.txt` | .github/workflows/ci.yml | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 163 |
| R43 | CI sets the Python default to 3.15 | .github/workflows/ci.yml | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 77 |
| R44 | Changelog README exists | changelog.d/README.md | fcbde10e0c293390bd9df8d62a5d61f158eca384 | present | 0 |
| R45 | Changelog README rule four, no fragment for an internal-only change | changelog.d/README.md | fcbde10e0c293390bd9df8d62a5d61f158eca384 | present | 58 |
| R46 | Precedent fragment exists for issue 4920 | changelog.d/issue-4920-ex-hardware-inventory-csv.md | 05befcb6b5e3f67c1554c1041d0d8d03d922abb7 | present | 0 |
| R47 | Runbook exists | documentation/noc-runbooks/MIST_NETCOOL_ALARM_INTEGRATION.md | f53313e142d735290a15f821962782e4c80dc9ef | present | 0 |
| R48 | Runbook gives the command `python -m scripts.netcool_runbook_smoke` | documentation/noc-runbooks/MIST_NETCOOL_ALARM_INTEGRATION.md | f53313e142d735290a15f821962782e4c80dc9ef | present | 1982 |
| R49 | Gate guard exists | tests/guardrails/test_ci_gate_triggers.py | 6ae30aa0f6a0ab008977b28df3ce728e3dd22411 | present | 0 |
| R50 | Gate guard names the workflow file `ci.yml` in `CI_WORKFLOW` | tests/guardrails/test_ci_gate_triggers.py | 6ae30aa0f6a0ab008977b28df3ce728e3dd22411 | present | 35 |
| R51 | Gate guard parses workflows through `_parse` | tests/guardrails/test_ci_gate_triggers.py | 6ae30aa0f6a0ab008977b28df3ce728e3dd22411 | present | 58 |
| R52 | Nested package guard exists | tests/guardrails/test_nested_package_structure.py | 5678277a376271483a6d340751e4c8ff7b5d92a3 | present | 0 |
| R53 | Nested package guard scans `src` only | tests/guardrails/test_nested_package_structure.py | 5678277a376271483a6d340751e4c8ff7b5d92a3 | present | 16 |
| R54 | Nested package guard limit is five children | tests/guardrails/test_nested_package_structure.py | 5678277a376271483a6d340751e4c8ff7b5d92a3 | present | 17 |
| R55 | Nested package guard excludes `__init__.py` from the module count | tests/guardrails/test_nested_package_structure.py | 5678277a376271483a6d340751e4c8ff7b5d92a3 | present | 119 |
| R56 | Nested package baseline exists | tests/guardrails/nested_package_baseline.json | 0d6c5ca933d83a4721c0bcc7220f69905fcf81f5 | present | 0 |
| R57 | Process folder baseline exists | tests/guardrails/process_folder_baseline.json | f3eb8a7b6c62f3154ac6fa867a8948504818798b | present | 0 |
| R58 | Spec route script exists | .specify/scripts/powershell/spec-route.ps1 | 37293a255f9b5de20ccb2b3ef0ad15717bab2826 | present | 0 |
| R59 | Base-5 route function `Get-SpecRadixSegments` exists | .specify/scripts/powershell/spec-route.ps1 | 37293a255f9b5de20ccb2b3ef0ad15717bab2826 | present | 4 |
| R60 | Spec template exists | .specify/templates/spec-template.md | 083ef123c7a2e56e21f3062173fb003258f927e2 | present | 0 |
| R61 | Plan template exists | .specify/templates/plan-template.md | 1a54553bd85cbef2178aa55efbeeb0c1942ffdde | present | 0 |
| R62 | Tasks template exists | .specify/templates/tasks-template.md | 7e5170324d41a6736c498d6b9fc83651f31d0778 | present | 0 |
| R63 | Checklist template exists | .specify/templates/checklist-template.md | 806657da09d1058823923e346a323b633114971a | present | 0 |
| R64 | Mist OpenAPI YAML exists | documentation/mist-api-openapi31yaml.yaml | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 0 |
| R65 | GET `/api/v1/self` has operation `getSelf` | documentation/mist-api-openapi31yaml.yaml | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 25490 |
| R66 | GET `/api/v1/orgs/{org_id}/alarms/search` has operation `searchOrgAlarms` | documentation/mist-api-openapi31yaml.yaml | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 5335 |
| R67 | Mist OpenAPI JSON exists, the package default | documentation/mist-api-openapi31json.json | 5f9f4ce94f812f0e818ee65f99f032118a28f56c | present | 0 |
| R68 | Dockerfile exists | Dockerfile | bc9249a19f6f181e7ea0e2c4b565a139d16d9253 | present | 0 |
| R69 | Dockerfile COPY sources hold no repository `scripts` folder | Dockerfile | bc9249a19f6f181e7ea0e2c4b565a139d16d9253 | absent | 70 |
| R70 | Reference record 4920 exists | specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv | 00922155516e4f21e34a0bf75613fae7ab481193 | present | 0 |
| R71 | Sibling record 4934 exists | specs/numbered/0/0/1/2/4/2/1/4/4934-mist-netcool-runbook | 294ae21b2248df93692af0b29a6e7df02c35231b | present | 0 |
| R72 | Route folder for 4945 is absent | specs/numbered/0/0/1/2/4/2/4/0 | none | absent | 0 |
| R73 | Record folder for 4945 is absent | specs/**/4945-* | none | absent | 0 |
| R74 | `FilterProbes.filter_verdict` is defined | scripts/netcool_runbook_smoke/checks/scope.py | bbf00175418cac91b8bea656173a37624b77a8dd | present | 111 |
| R75 | `FilterProbes.record` is defined | scripts/netcool_runbook_smoke/checks/scope.py | bbf00175418cac91b8bea656173a37624b77a8dd | present | 149 |
| R76 | `ScopeChecks.smk_08` is defined | scripts/netcool_runbook_smoke/checks/scope.py | bbf00175418cac91b8bea656173a37624b77a8dd | present | 209 |
| R77 | `ScopeChecks.smk_09` is defined | scripts/netcool_runbook_smoke/checks/scope.py | bbf00175418cac91b8bea656173a37624b77a8dd | present | 242 |
| R78 | `ScopeChecks._site_part` is defined | scripts/netcool_runbook_smoke/checks/scope.py | bbf00175418cac91b8bea656173a37624b77a8dd | present | 279 |
| R79 | `SiteListing.first_site` is defined | scripts/netcool_runbook_smoke/checks/scope.py | bbf00175418cac91b8bea656173a37624b77a8dd | present | 338 |
| R80 | `InventoryReader.count_sum` is defined | scripts/netcool_runbook_smoke/checks/scope.py | bbf00175418cac91b8bea656173a37624b77a8dd | present | 406 |
| R81 | `InventoryReader.webhook_part` is defined | scripts/netcool_runbook_smoke/checks/scope.py | bbf00175418cac91b8bea656173a37624b77a8dd | present | 457 |
| R82 | `InventoryChecks.smk_10` is defined | scripts/netcool_runbook_smoke/checks/scope.py | bbf00175418cac91b8bea656173a37624b77a8dd | present | 528 |
| R83 | `InventoryChecks._judge` is defined | scripts/netcool_runbook_smoke/checks/scope.py | bbf00175418cac91b8bea656173a37624b77a8dd | present | 559 |
| R84 | `SearchChecks.smk_06` is defined | scripts/netcool_runbook_smoke/checks/searches.py | 9d9a28dbb08b4c73645f0cd3e7ced8eac68e08ef | present | 448 |
| R85 | `SearchChecks.smk_07` is defined | scripts/netcool_runbook_smoke/checks/searches.py | 9d9a28dbb08b4c73645f0cd3e7ced8eac68e08ef | present | 482 |
| R86 | `CallGovernor._attempt` is defined | scripts/netcool_runbook_smoke/client.py | da54b0c22449362ff84a8e2766b2942037283c26 | present | 428 |
| R87 | `CallGovernor._run_with_timeout` is defined | scripts/netcool_runbook_smoke/client.py | da54b0c22449362ff84a8e2766b2942037283c26 | present | 471 |
| R88 | Class `SmokeSettings` starts the classes of `__main__.py` | scripts/netcool_runbook_smoke/__main__.py | 9762671c48a4767c8a64f8764eefcfef12643a44 | present | 54 |
| R89 | Class `CallRecord` starts the classes of `client.py` | scripts/netcool_runbook_smoke/client.py | da54b0c22449362ff84a8e2766b2942037283c26 | present | 33 |
| R90 | Class `TracebackFreeFormatter` starts the classes of `command.py` | scripts/netcool_runbook_smoke/command.py | 6d12bd8fd9b9f19bdbd6dc8701773dea327debbf | present | 31 |
| R91 | Class `MarkdownTables` starts the classes of `documents.py` | scripts/netcool_runbook_smoke/documents.py | ce21576501a683dd4b115ddc06488b1eba4e345e | present | 25 |
| R92 | Class `CheckStatus` starts the classes of `checks/__init__.py` | scripts/netcool_runbook_smoke/checks/__init__.py | 2079ae9db2bf49182397116e6d463a5e1762b997 | present | 38 |
| R93 | Class `CatalogStore` starts the classes of `checks/catalogs.py` | scripts/netcool_runbook_smoke/checks/catalogs.py | 9b3a94c197cb14cd533ac30df1fae04df74237cb | present | 25 |
| R94 | Class `DocumentLoader` starts the classes of `checks/identity.py` | scripts/netcool_runbook_smoke/checks/identity.py | 91fdd0d744dc0b480d0ccba5c61d723887e00082 | present | 34 |
| R95 | Class `FilterProbes` starts the classes of `checks/scope.py` | scripts/netcool_runbook_smoke/checks/scope.py | bbf00175418cac91b8bea656173a37624b77a8dd | present | 28 |
| R96 | Class `SearchObservations` starts the classes of `checks/searches.py` | scripts/netcool_runbook_smoke/checks/searches.py | 9d9a28dbb08b4c73645f0cd3e7ced8eac68e08ef | present | 33 |
| R97 | Class `SessionOpener` starts the classes of `checks/support.py` | scripts/netcool_runbook_smoke/checks/support.py | d14a4ac42d3717ece9af28d17997a3d6e83e376a | present | 27 |
| R98 | REST GET runs through `self.session.mist_get(uri, query)` | scripts/netcool_runbook_smoke/client.py | da54b0c22449362ff84a8e2766b2942037283c26 | present | 496 |
| R99 | The client imports `urllib.parse` for link parsing | scripts/netcool_runbook_smoke/client.py | da54b0c22449362ff84a8e2766b2942037283c26 | present | 25 |
| R100 | Session default is `mistapi.APISession` | scripts/netcool_runbook_smoke/__main__.py | 9762671c48a4767c8a64f8764eefcfef12643a44 | present | 587 |
| R101 | OpenAPI default names the JSON file | scripts/netcool_runbook_smoke/__main__.py | 9762671c48a4767c8a64f8764eefcfef12643a44 | present | 231 |
| R102 | Evidence default path lies under `test-artifacts` | scripts/netcool_runbook_smoke/documents.py | ce21576501a683dd4b115ddc06488b1eba4e345e | present | 734 |
| R103 | Package logger prefix `scripts.netcool_runbook_smoke` | scripts/netcool_runbook_smoke/command.py | 6d12bd8fd9b9f19bdbd6dc8701773dea327debbf | present | 63 |

Row count: 103. The `analysis.md` file, the `STATUS.json` file, and the `summary.md` file cite the same count.

## Sources

| Source | Path or URL | Used for |
| - | - | - |
| Issue #4945 | `gh issue view 4945 -R jmorrison-juniper/MistHelper` | Requirements, scope, acceptance, out of scope |
| Issue #4937 | `gh issue view 4937 -R jmorrison-juniper/MistHelper` (closed) | Written exception for the folder rule |
| Issue #4944 | `gh issue list` search result (open) | Folder debt tracking |
| Issue #4934 | Record R71 and the issue body of #4945 | Feature origin of the package |
| PR search for 4945 | `gh pr list -R jmorrison-juniper/MistHelper --state all --search "4945"` | Empty result, so no linked pull request |
| AGENTS.md | `AGENTS.md` (repository root), blob `44a9afff` | Writing style, class rules, branch and commit rules |
| Copilot instructions | `.github/copilot-instructions.md`, blob `f1ec2a46` | Local gate table, child-count convention, Spec Kit layout |
| Constitution | `.specify/memory/constitution.md`, blob `4584997a` | Principles I, IV, VI, VII, governance |
| Templates | `.specify/templates/*.md`, blobs listed in R60 to R63 | Record shape |
| Reference record | `specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv` (row R70) | Shape of `design/` and checklists |
| Spec route script | `.specify/scripts/powershell/spec-route.ps1` (rows R58 and R59) | Base-5 route rule. The route `0/0/1/2/4/2/4/0` for 4945 follows the rule: 4945 is `124240` in base 5. |
| Package code | Rows R01 to R11 and R74 to R103 | Structure and function measures |
| Test modules | Rows R12 to R16 | Test counts and imports |
| CI workflow | `.github/workflows/ci.yml` (rows R17 to R25, R42, R43) | Gate variables and commands |
| pyproject | `pyproject.toml` (rows R26 to R30) | Exclusions and the mypy precedent |
| Nested guard | `tests/guardrails/test_nested_package_structure.py` (rows R52 to R55) | Child-count rule and file location |
| Gate guard | `tests/guardrails/test_ci_gate_triggers.py` (rows R49 to R51) | Location for the gate guard |
| Changelog README | `changelog.d/README.md` (rows R44 to R46) | Fragment naming and the internal-only rule |
| Runbook | `documentation/noc-runbooks/MIST_NETCOOL_ALARM_INTEGRATION.md` (rows R47 and R48) | Command path that must keep working |
| Dockerfile | `Dockerfile` (rows R68 and R69) | Image contents |
| Mist OpenAPI | `documentation/mist-api-openapi31yaml.yaml` and `documentation/mist-api-openapi31json.json` (rows R64 to R67) | Endpoint operations |
| mistapi SDK (local) | `.venv\Lib\site-packages\mistapi\__api_request.py` line 260 (`mist_get`), `.venv\Lib\site-packages\mistapi\__api_session.py` line 52 (`class APISession`), `.venv\Lib\site-packages\mistapi-0.64.1.dist-info` | Method names and the pin |
| misthelper_devtools (local) | `.venv\Lib\site-packages\misthelper_devtools\speckit_task_audit.py` lines 14 to 34 (patterns `CHECKBOX_RE`, `TASK_ID_RE`, `STATUS_RE`) | Task format for the advisory audit |
| Gate executables (local) | `.venv\Scripts\complexity-gate.exe`, `symbol-diff.exe`, `vulture.exe`, `radon.exe`, `interrogate.exe`, `pydocstyle.exe`, `ste-linter.exe` | Gate commands |

## Unverified

Each item below lacks evidence in this research. The plan does not depend on any item for a decision.

1. **The 227 test count of the issue.** The static count is 194 (rows R12 to R16). The collected count is not measured, because the research forbids test runs. T003 measures it.
2. **The comment sample of the issue.** The issue reports 12 weak test comments out of 20 and 5 weak package comments out of 25. The sample is not reproduced. T035 repeats the audit with a fixed seed.
3. **The mypy strict result for the package.** Not measured. T004 measures it.
4. **The radon, Vulture, pydocstyle, and Interrogate results for the package.** Not measured. T004 measures them.
5. **The package coverage.** Not measured. T005 measures it.
6. **The explicit Ruff and Bandit run on the package.** Not measured. The count step decides it, and TEST-08 tests it.
7. **The pinned versions of the gate tools in `requirements-dev.txt`.** The file is not read. CI installs it (row R42).
8. **The test-quality baseline entries of the five test modules.** The file `.github/test-quality-baseline.json` is not read. T-LOCAL-GATES reads it.
9. **The content of PR #4941.** The issue names it as the origin pull request. The local commit `f03c6c9` has a subject that names PR #4941. The remote state of PR #4941 is not read, and no claim depends on it.
10. **The title and state of issue #4934.** The record exists on `main` (row R71). The issue state is not used.
11. **The `pytest-chunks` and `test_script_imports.py` behavior with the moved modules.** `ci.yml` line 303 runs `tests/unit/scripts/test_script_imports.py` directly. The file is not read. T-LOCAL-GATES runs it.
12. **The Python interpreter version inside `.venv`.** The CI default is 3.15 (row R43). The local interpreter version is not read.
