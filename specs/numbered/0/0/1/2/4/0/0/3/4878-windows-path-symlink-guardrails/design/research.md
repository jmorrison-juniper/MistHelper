# Research: Windows Path and Symlink Guardrails

Each decision lists the chosen option, the reason, and the alternatives. Remote facts come from reads of `main` at commit `f03c6c9b36d612a48d7b9652998c2fd87dd777ca`. Local facts come from read-only commands on the same commit. Each remote row names a path, a blob or object SHA, and a line.

## Decisions

## D-1. Test-only scope

- **Decision**: Change three test modules and add one changelog fragment. Change no file under `src/`.
- **Rationale**: Each failure sits in test code. The symlink call sits in the test body (R-05). The Git value and the message text sit in test assertions and helpers (R-15, R-19).
- **Alternatives considered**:
  - Change path handling in product code. Rejected, because the failing comparisons are test assertions.
  - Mark the three guards as skipped on Windows. Rejected, because skips hide the real failures.
- **Risk**: Low. Each guard keeps its checks and changes only its comparison rules.

## D-2. Skip only for WinError 1314

- **Decision**: The symlink method skips only when `winerror` equals 1314. It re-raises every other `OSError`.
- **Rationale**: Microsoft defines 1314 as ERROR_PRIVILEGE_NOT_HELD, "A required privilege is not held by the client" (S-3). The issue acceptance requires a skip for this host limit. A narrow match keeps other faults visible. The AGENTS rule says a guard that cannot read its input fails (R-53).
- **Alternatives considered**:
  - Skip on any `OSError`. Rejected, because it hides an unrelated fault.
  - Call `pytest.fail`, as the missing `pwsh` checks do (R-12). Rejected, because the issue asks for a skip, and the privilege is a host limit.
  - Use a module-level `skipif` probe. Rejected, because it adds a module-level name and creates a probe file.
- **Risk**: A different Windows error on the symlink call fails the test. The failure shows the cause. A skip can count as a pass in summaries (R-76). The skip reason prints under `-rs`, and the Linux job runs the case.

## D-3. Log the cause before the skip

- **Decision**: Log the link action at info before it runs and at debug after it. Log the cause at error level before the skip.
- **Rationale**: The constitution requires action logging, including an error log for each exception (R-30). The skip logs at error level, as the rule requires. The AGENTS rule requires a skip to print its cause (R-53).
- **Alternatives considered**:
  - Use warning level. Rejected, because the exception is an error line under the AGENTS rule.
  - Log nothing and rely on the skip reason. Rejected, because the constitution requires the logging.
- **Risk**: None. The log lines use `%s` formatting and ASCII text (R-27).

## D-4. Compare the Git root as a path value

- **Decision**: Store the `rev-parse --show-toplevel` output. Assert `Path(top_level) == repository.root.resolve()`.
- **Rationale**: `FixtureRepository.git` returns stripped stdout (R-13). Git on Windows prints forward slashes (L-4). Path equality on Windows lowercases each string and normalizes the separator (S-4). The comparison needs no filesystem call.
- **Alternatives considered**:
  - Compare `as_posix()` values on both sides. Rejected, because the text depends on the drive letter case.
  - Use `os.path.samefile`. Rejected, because it adds filesystem calls for a text comparison.
- **Risk**: A short 8.3 path from Git still differs. The local check did not observe that form (UV-4).

## D-5. One separator style for the missing-root message

- **Decision**: Build `missing_paths` with `as_posix()`, and escape `missing_root.as_posix()` in the expected pattern.
- **Rationale**: The message formats a Python list, so backslashes appear doubled (R-19). The pattern escapes one form only (R-20). The local search found no other reader of the message (S-14).
- **Alternatives considered**:
  - Parse the list repr in the test. Rejected, because it depends on repr escaping.
  - Join the paths with a comma. Rejected, because the backslashes still need escaping in the pattern.
  - Change only the pattern. Rejected, because the message still contains doubled backslashes.
- **Risk**: A reader outside the test would see forward slashes. None exists at HEAD (S-14).

## D-6. A method helper and a function-local import

- **Decision**: Put the symlink logic in method `SpecCommandFixture.symlink`. Import `logging` inside the method.
- **Rationale**: `symbol-diff` reads only top-level statements, and it reports each added name as a change (S-7). A module-level import would add the name `logging`, so the Symbols gate would fail (R-51). The test-quality analyzer flags only module-scope public functions (S-8). A method avoids that rule. Ruff selects no import-position rule, so the local import passes lint (R-67).
- **Alternatives considered**:
  - Module-level helper function. Rejected, because it adds a module-level name.
  - Module-level `import logging`. Rejected, because the Symbols gate reports it.
- **Risk**: A function-local import is unusual. The import has an inline comment that names the reason.

## D-7. No new top-level test name or class

- **Decision**: Add no test function and no test class. The existing parametrized case and the one-off check verify the new behavior. Quickstart section 2.3 holds the one-off check.
- **Rationale**: The constitution forbids a new direct child under a noncompliant parent (R-24). The test module already holds more than five top-level names (R-10). A new test function would add a child to that module.
- **Alternatives considered**:
  - Add monkeypatch tests to the same module. Rejected, because each test is a new top-level name.
  - Create a new test package under `tests\guardrails`. Rejected, because the new directory is a child of a noncompliant parent.
- **Risk**: The skip branch has no Linux case in CI. Analysis item U-1 records the follow-up.

## D-8. Add the changelog fragment

- **Decision**: Add `changelog.d\issue-4878-windows-path-symlink-guardrails.md` with a `Fixed` bullet.
- **Rationale**: The constitution requires one fragment for each change (R-32). The copilot instructions limit the fragment to a user-visible change (R-42). The changelog README exempts an internal change (R-54). This decision follows the strictest rule, and analysis item A-2 records the conflict.
- **Alternatives considered**:
  - Add no fragment. Rejected, because the constitution uses the word MUST.
  - Name the fragment `pr-4878.md` after the pull request opens. Rejected, because the first name must stay fixed, and a rename creates a delete and an add (R-55).
- **Risk**: The release notes contain one internal entry. The entry is short and names the issue.

## D-9. Route and slug

- **Decision**: Store the record at `specs\numbered\0\0\1\2\4\0\0\3\4878-windows-path-symlink-guardrails`. The slug is `windows-path-symlink-guardrails`.
- **Rationale**: The base-5 digits of 4878 give `0 0 1 2 4 0 0 3` (L-9). The route function joins eight digits under `numbered` (R-22, R-23). The copilot instructions require the numbered route (R-41). The route folder is absent on `main` (R-70).
- **Alternatives considered**:
  - Store the record on the timestamp route under `specs\live`. Rejected, because the constitution assigns numeric records to `specs\numbered` (R-31).
  - Choose another slug. Rejected, because the slug has no effect on the route, and this slug names the subject.
- **Risk**: None. The route guard tests the formula, not this folder (R-11).

## D-10. Commit type and labels

- **Decision**: Use the commit subject `fix(tests): skip symlink guard without privilege and compare paths as values`. Add the scope label `tests`. Keep labels `bug` and `test`.
- **Rationale**: The constitution lists `fix` as a commit type (R-34). The copilot instructions map a pytest failure to the labels `bug` and `test` (R-44). The repository has a label named `tests` (S-12).
- **Alternatives considered**:
  - Use the type `test`. Rejected, because the issue is a defect in the guard tests, and the label pipeline names `bug`.
  - Remove the label `test`. Rejected, because the pipeline names it.
- **Risk**: None.

## D-11. Omit the contracts folder

- **Decision**: Omit `design\contracts\`. Write the data model as one "Not applicable" line.
- **Rationale**: The change alters no menu, CLI, output column, or API shape. The skip text is an internal diagnostic and not a public interface.
- **Alternatives considered**:
  - Write a contract for the skip text. Rejected, because no caller reads the text.
  - Write the data model as an entity table. Rejected, because the change defines no entity.
- **Risk**: None.

## Remote Verification

Each row is one check. The table holds 76 rows, and the same count appears in STATUS.json and in the summary.

| ID | Claim | Path | Ref | Blob or object SHA | Result | Line |
| - | - | - | - | - | - | - |
| R-01 | Issue commit 23379f0e0 is on main, ahead by 10 and behind by 0 | commit 23379f0e075557cd5c0761a79f23ad8d3583e296 | main | 23379f0e075557cd5c0761a79f23ad8d3583e296 | present | 0 |
| R-02 | Main head is f03c6c9b36d612a48d7b9652998c2fd87dd777ca | commits/main | main | f03c6c9b36d612a48d7b9652998c2fd87dd777ca | present | 0 |
| R-03 | Symlink case test is defined | tests/guardrails/test_spec_route_contract.py | main | b174399ad5f23f4844dc442954bf203be07342f3 | present | 287 |
| R-04 | Symlink branch begins with the case check | tests/guardrails/test_spec_route_contract.py | main | b174399ad5f23f4844dc442954bf203be07342f3 | present | 294 |
| R-05 | Symlink creation calls symlink_to | tests/guardrails/test_spec_route_contract.py | main | b174399ad5f23f4844dc442954bf203be07342f3 | present | 296 |
| R-06 | Module has no logging import | tests/guardrails/test_spec_route_contract.py | main | b174399ad5f23f4844dc442954bf203be07342f3 | absent | 0 |
| R-07 | SpecCommandFixture class is defined | tests/guardrails/test_spec_route_contract.py | main | b174399ad5f23f4844dc442954bf203be07342f3 | present | 159 |
| R-08 | SpecCommandFixture.feature is a method | tests/guardrails/test_spec_route_contract.py | main | b174399ad5f23f4844dc442954bf203be07342f3 | present | 184 |
| R-09 | SpecCommandFixture.run starts pwsh through subprocess | tests/guardrails/test_spec_route_contract.py | main | b174399ad5f23f4844dc442954bf203be07342f3 | present | 176 |
| R-10 | Module holds more than five top-level names, lines 14 to 514 | tests/guardrails/test_spec_route_contract.py | main | b174399ad5f23f4844dc442954bf203be07342f3 | present | 287 |
| R-11 | test_radix_route_is_stable pins base-5 routes | tests/guardrails/test_spec_route_contract.py | main | b174399ad5f23f4844dc442954bf203be07342f3 | present | 45 |
| R-12 | Missing pwsh fails with pytest.fail, repeated at lines 94, 114, 149, 174, 454, and 468 | tests/guardrails/test_spec_route_contract.py | main | b174399ad5f23f4844dc442954bf203be07342f3 | present | 68 |
| R-13 | FixtureRepository.git returns stripped stdout | tests/guardrails/local_test_quality_loop/fixtures.py | main | 9c3228edb6070ade70ae4a1702927f81d3821c13 | present | 168 |
| R-14 | Git root guard test is defined | tests/guardrails/local_test_quality_loop/test_scope.py | main | 2c3645416c5c96cd6d1a788221a1ce04376ef447 | present | 630 |
| R-15 | Git root assertion compares a string | tests/guardrails/local_test_quality_loop/test_scope.py | main | 2c3645416c5c96cd6d1a788221a1ce04376ef447 | present | 643 |
| R-16 | test_scope.py imports logging | tests/guardrails/local_test_quality_loop/test_scope.py | main | 2c3645416c5c96cd6d1a788221a1ce04376ef447 | present | 6 |
| R-17 | Missing-root guard test is defined | tests/guardrails/test_analytics_package_structure.py | main | ee79f1f39ecf1621f7e303aa452979091d2922b4 | present | 171 |
| R-18 | Inspector formats missing paths with str | tests/guardrails/test_analytics_package_structure.py | main | ee79f1f39ecf1621f7e303aa452979091d2922b4 | present | 74 |
| R-19 | Inspector message embeds a Python list | tests/guardrails/test_analytics_package_structure.py | main | ee79f1f39ecf1621f7e303aa452979091d2922b4 | present | 75 |
| R-20 | Expected pattern uses str(missing_root) | tests/guardrails/test_analytics_package_structure.py | main | ee79f1f39ecf1621f7e303aa452979091d2922b4 | present | 177 |
| R-21 | Analytics module defines LOGGER | tests/guardrails/test_analytics_package_structure.py | main | ee79f1f39ecf1621f7e303aa452979091d2922b4 | present | 45 |
| R-22 | Get-SpecRadixSegments uses base 5 | .specify/scripts/powershell/spec-route.ps1 | main | 37293a255f9b5de20ccb2b3ef0ad15717bab2826 | present | 17 |
| R-23 | Resolve-SpecFeaturePath routes numbered records | .specify/scripts/powershell/spec-route.ps1 | main | 37293a255f9b5de20ccb2b3ef0ad15717bab2826 | present | 34 |
| R-24 | Constitution Principle I sets the hierarchy limit of five children | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 40 |
| R-25 | Constitution Principle II is class-based architecture | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 91 |
| R-26 | Constitution Principle III is safety-first | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 113 |
| R-27 | Constitution Principle IV is the full deployment pipeline | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 143 |
| R-28 | Constitution Principle V is observability and logging | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 182 |
| R-29 | Constitution Principle VI requires inline comments | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 204 |
| R-30 | Constitution Principle VII requires action logging | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 235 |
| R-31 | Constitution requires the numbered base-5 route | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 58 |
| R-32 | Constitution requires one fragment for each change | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 409 |
| R-33 | Constitution requires Python 3.15 or newer | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 278 |
| R-34 | Constitution lists fix as a commit type | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 157 |
| R-35 | Constitution requires pathlib or os.path.join for paths | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 310 |
| R-36 | Constitution names Podman as the container runtime | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 300 |
| R-37 | Constitution lists Windows 11 for local development | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 363 |
| R-38 | Constitution requires fixing security findings, not suppressing them | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 373 |
| R-39 | Constitution sets the SpecKit escalation rule | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 420 |
| R-40 | Constitution sets the multi-agent git workflow | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 453 |
| R-41 | Copilot instructions require the numbered route | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 159 |
| R-42 | Copilot instructions limit the fragment rule to user-visible changes | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 451 |
| R-43 | Copilot instructions trigger the container build on pushes that change product files, or on manual dispatch | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 473 |
| R-44 | Copilot instructions map a pytest failure to labels bug and test | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 445 |
| R-45 | Compile gate row | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 57 |
| R-46 | Lint gate row runs ruff check | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 58 |
| R-47 | Format gate row runs black check | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 59 |
| R-48 | Tests gate row runs pytest on the changed file | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 61 |
| R-49 | Test quality gate row runs the analyzer | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 65 |
| R-50 | Security lint gate row runs bandit | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 67 |
| R-51 | Symbols gate row runs symbol-diff with exit code 0 | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 73 |
| R-52 | STE gate row lists five instruction and guide files | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 74 |
| R-53 | AGENTS rule says a skip prints its cause | AGENTS.md | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 143 |
| R-54 | Changelog README exempts an internal-only change | changelog.d/README.md | main | fcbde10e0c293390bd9df8d62a5d61f158eca384 | present | 58 |
| R-55 | Changelog README keeps the first fragment name | changelog.d/README.md | main | fcbde10e0c293390bd9df8d62a5d61f158eca384 | present | 32 |
| R-56 | Changelog guard defines the issue-form name pattern | tests/guardrails/test_changelog_fragment_policy.py | main | dbd5e8776797f12536b3bc2bd613143b85f3fc4a | present | 39 |
| R-57 | Changelog guard requires a heading and a bullet | tests/guardrails/test_changelog_fragment_policy.py | main | dbd5e8776797f12536b3bc2bd613143b85f3fc4a | present | 192 |
| R-58 | Changelog guard uses pytest.skip with a reason | tests/guardrails/test_changelog_fragment_policy.py | main | dbd5e8776797f12536b3bc2bd613143b85f3fc4a | present | 256 |
| R-59 | CI runs the changelog guard | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 298 |
| R-60 | CI pytest scope includes tests/guardrails | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 255 |
| R-61 | MYPY_PATHS excludes tests | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 93 |
| R-62 | VULTURE_PATHS excludes tests | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 101 |
| R-63 | PYDOCSTYLE_PATHS excludes tests | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 104 |
| R-64 | INTERROGATE_PATHS excludes tests | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 107 |
| R-65 | Bandit exclude list names tests | pyproject.toml | main | eca34c826ea44ba4f2faefc07d04c2c117e99751 | present | 503 |
| R-66 | Ruff line length is 120 | pyproject.toml | main | eca34c826ea44ba4f2faefc07d04c2c117e99751 | present | 202 |
| R-67 | Ruff selects E, F, W, I, UP, B, G, PLW1514, and RUF100 | pyproject.toml | main | eca34c826ea44ba4f2faefc07d04c2c117e99751 | present | 209 |
| R-68 | PR template requires one guard failing path | .github/PULL_REQUEST_TEMPLATE.md | main | ed03e8f36f20962d9c7bbd74cde192d5adfdcc77 | present | 12 |
| R-69 | PR template requires one changelog fragment | .github/PULL_REQUEST_TEMPLATE.md | main | ed03e8f36f20962d9c7bbd74cde192d5adfdcc77 | present | 36 |
| R-70 | Route specs/numbered/0/0/1/2/4/0 is absent | specs/numbered/0/0/1/2/4/0 | main | none | absent | 0 |
| R-71 | Reference record spec.md is present | specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv/spec.md | main | 83b950279e45704943ad6942d23c8fc99cced492 | present | 1 |
| R-72 | Active-path scanner keeps tracked .md files outside specs | tests/guardrails/test_analytics_package_structure.py | main | ee79f1f39ecf1621f7e303aa452979091d2922b4 | present | 128 |
| R-73 | Route parent holds child 1 on main | specs/numbered/0/0/1/2/4/1 | main | b86cdb8134240596ecab84c015df8b79670b31b7 | present | 0 |
| R-74 | Route parent holds child 2 on main | specs/numbered/0/0/1/2/4/2 | main | 9b7dd503cf4443e56320e69b8aa83eb3a748fa7b | present | 0 |
| R-75 | The symlink case runs check-prerequisites.ps1 through the fixture | tests/guardrails/test_spec_route_contract.py | main | b174399ad5f23f4844dc442954bf203be07342f3 | present | 298 |
| R-76 | Quality gates warn that pytest reports a skip as a pass, citing issue #2241 | documentation/quality-gates.md | main | 6776d334cca5d9b43273473a06da367a65605c6d | present | 76 |

Provenance: local `git hash-object` equals the remote blob SHA for nine files: `test_spec_route_contract.py`, `test_scope.py`, `test_analytics_package_structure.py`, `spec-route.ps1`, `AGENTS.md`, `copilot-instructions.md`, `constitution.md`, `quality-gates.md`, and `ci.yml` (S-19). Local line numbers for those files equal the remote line numbers. The other rows come from remote content reads of the same commit.

## Local Verification

These checks are read-only and not counted in the remote table.

- L-1: `git rev-parse HEAD` returns `f03c6c9b36d612a48d7b9652998c2fd87dd777ca`, and the branch is `main` (S-13).
- L-2: `git status --short` lists five modified files outside this issue: `src/foundation/support/utils/logger_utils.py`, `src/interfaces/wan_performance/collection/request_admission.py`, `src/mist/intelligence/reports/subscription_expiry/client.py`, `tests/unit/marvis/mist/intelligence/reports/audits/credentials/subscription_expiry/test_client.py`, and `tests/unit/wan_dashboard/wan_performance/collection/test_request_admission.py` (S-13).
- L-3: `git merge-base --is-ancestor 23379f0e075557cd5c0761a79f23ad8d3583e296 HEAD` exits 0 (S-13).
- L-4: `git rev-parse --show-toplevel` prints `C:/Users/jmorrison/OneDrive - Hewlett Packard Enterprise/Code/MistHelper`, with forward slashes (S-9).
- L-5: `git grep` at HEAD finds the analytics message only at `tests/guardrails/test_analytics_package_structure.py` lines 75 and 173 (S-14).
- L-6: `git ls-tree HEAD changelog.d/` lists `issue-1794-analytics-exceptions.md`, which is a naming precedent (S-15).
- L-7: `.venv\pyvenv.cfg` names Python 3.15.2 (S-18).
- L-8: The venv holds `pytest-9.2.0.dist-info` (S-6).
- L-9: The base-5 digits of 4878 are `0 0 1 2 4 0 0 3`. The check is 1 times 5 to the fifth, plus 2 times 5 to the fourth, plus 4 times 5 cubed, plus 3.
- L-10: A recursive search of `specs\` finds no folder whose name starts with `4878-`. No legacy record exists, so `existing_record.found` is `false`.
- L-11: A search of `documentation\architecture.md`, `development-setup.md`, `container-deployment.md`, and `operator-guide.md` finds no symlink or Windows privilege guidance. The development setup page describes the `.venv` bootstrap at its line 40.

## Sources

- S-1: `AGENTS.md` at the repository root, blob `44a9afffb5bd6f774973a845d27343e4e528b6ad` (R-53).
- S-2: `.github\copilot-instructions.md`, blob `f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179` (R-41 to R-52).
- S-3: Microsoft, "System Error Codes (1300-1699) (WinError.h)", https://learn.microsoft.com/en-us/windows/win32/debug/system-error-codes--1300-1699-. Fetched 2026-11-26. Entry 1314 (0x522) reads "A required privilege is not held by the client."
- S-4: Python 3.15.2 standard library, `C:\Users\jmorrison\AppData\Local\Python\pythoncore-3.15-64\Lib\pathlib\__init__.py`, lines 199 to 208 (`_str_normcase` lowercases on Windows) and lines 217 to 220 (`__eq__`).
- S-5: Python 3.15.2 standard library, `C:\Users\jmorrison\AppData\Local\Python\pythoncore-3.15-64\Lib\ntpath.py`, line 599 (`if ex.winerror in allowed_winerror:`), which shows that the Windows `OSError` exposes `winerror`.
- S-6: pytest 9.2.0, `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\.venv\Lib\site-packages\_pytest\outcomes.py`, line 39 (`class Skipped(OutcomeException)`).
- S-7: The symbol-diff comparator is `.venv\Lib\site-packages\misthelper_devtools\symbol_diff\comparator.py`. Lines 64, 110 to 116, 120 to 129, and 161 to 166 show the top-level rule, the added names, and the imports.
- S-8: misthelper_devtools test-quality analyzer, `.venv\Lib\site-packages\misthelper_devtools\test_quality_analyzer\detection\untested.py`, lines 97 (module-scope names only) and 139 to 140 (names that start with an underscore are skipped).
- S-9: Local `git rev-parse --show-toplevel` on this host, run 2026-11-26.
- S-10: GitHub issue #4878, read with `gh issue view`. The issue has labels `bug` and `test`, and no comments.
- S-11: GitHub pull request #4880, merged 2026-11-22, read with `gh pr view`. Its body names #4877, #4878, and #4879 as follow-ups. Its status checks show 42 successful and 9 skipped.
- S-12: GitHub labels, read with `gh label list`. The labels `tests`, `in-progress`, `bug`, and `test` exist.
- S-13: Local checkout on branch `main`, tracking `origin/main`, at `f03c6c9b36d612a48d7b9652998c2fd87dd777ca`, with five modified files (L-1, L-2, L-3).
- S-14: Local `git grep` at HEAD (L-5).
- S-15: Local `git ls-tree` at HEAD (L-6).
- S-16: Reference record `specs\numbered\0\0\1\2\4\1\4\0\4920-ex-hardware-inventory-csv`, read for shape only.
- S-17: Validator `spec-drafts\_meta\validate-drafts.ps1`, read-only, used as a final self-check.
- S-18: `.venv\pyvenv.cfg` (L-7).
- S-19: Local `git hash-object` for nine target files, each equal to the remote blob SHA listed in the remote table.

## Unverified

- UV-1: The three failures occur on the reporter host. Reason: rule 2 forbids a test run. Source: the issue text (S-10). Task T001 verifies this.
- UV-2: Python raises the `winerror` attribute on the symlink `OSError` on Windows. Reason: no Windows run. Evidence: S-5. Task T001 and quickstart section 2.3 verify this.
- UV-3: The skip reason prints in the `-rs` summary. Reason: no run. Evidence: S-6. Success criterion SC-001 verifies this.
- UV-4: Git on the reporter host never prints an 8.3 short path for the root. Reason: not observed. Task T-LOCAL-GATES verifies this on Windows.
- UV-5: Linux CI runs the symlink case without a skip. Reason: the run has not started. Task T-REMOTE-CI verifies this.
- UV-6: The test-quality analyzer reports zero new findings. Reason: not run. Task T-PR verifies this after the commit.
- UV-7: `symbol-diff` reports no module-level name change for each changed file. Reason: not run. Evidence: S-7. Task T-LOCAL-GATES verifies this.
- UV-8: The log lines in quickstart section 2.2 appear as described. Reason: not run. Task T-LOCAL-GATES verifies this.
