# Research: Isolate Marvis Alarm Handling Modules

Each decision lists the chosen option, the other options, the reason, and the risk. Each fact cites a remote row (R##), a legacy row (L#), a local evidence row (E-#), or an Unverified item (U-#). Remote facts come from `main` at commit `f03c6c9b36d612a48d7b9652998c2fd87dd777ca`, checked on 2026-11-26. Remote evidence outranks local evidence.

## Sources

Repository paths read through remote contents or remote trees:

- `AGENTS.md`, `.github/copilot-instructions.md`, `.specify/memory/constitution.md`, `.specify/scripts/powershell/spec-route.ps1`, `.github/workflows/ci.yml`, `changelog.d/README.md`, `documentation/quality-gates.md`.
- Marvis modules and tests under `src/mist/intelligence/marvis/actions/` and `tests/unit/marvis/actions/`.
- Guards under `tests/guardrails/`, including `test_changelog_fragment_policy.py`.
- `documentation/marvis-actions-api-endpoints.md`, `documentation/menu-api/interactive-safe.md`, and `documentation/mist-api-openapi31yaml.yaml`.
- The reference record `specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv/`.
- The historical record `specs/3339-marvis-alarm-join/`.

Local files read in the shared checkout, with read-only views and searches: the same paths, plus `.venv\Lib\site-packages\mistapi\api\v1\orgs\alarms.py` and `.venv\Lib\site-packages\mistapi-0.64.1.dist-info`.

Documentation read in full or in part: `documentation/quality-gates.md` (full), `documentation/architecture.md` (search), `documentation/development-setup.md` (search), `documentation/container-deployment.md` (search), and `documentation/operator-guide.md` (search). Operator guide lines 27 to 36 describe menu 270 and need no change. The container guide line 141 names the test-container section, which this change does not need.

Mist API coverage files: `documentation/MIST_API_GET_ENDPOINTS.md` and `documentation/MIST_API_MISSING_ENDPOINTS.md` each hold two lines that name `alarms/search` or `alarms/ack`. No claim in this record relies on those files. The OpenAPI rows R37 to R39 carry the endpoint evidence.

No URL was fetched. No web source was used.

No skill was loaded. The brief names skills for Podman and for Juniper device behavior. This change has neither.

## Linked work

- A search for `4008` in pull requests returned PR #4372 (merged 2026-10-20). Its body matches `4008` only inside a session identifier. PR #4372 is not linked (R76).
- Issue comments name PR #4557 (merged 2026-11-05, R74), PR #4607 (merged 2026-11-13, R75), and PR #4208 (open, R44).
- A scan of seven open pull requests against the candidate file set found one overlap, PR #4208 (R77).
- GitHub compare results: commit `ae3a6af8` is 401 commits behind main, commit `944a44846` is 43 behind, and commit `b571d2e7` is 43 behind. Each is diverged (R45, R68, and R69).
- The preserved commit `ae3a6af8` heads archive branch `archive/laptop-20261121/jmorrison-juniper-refactor-4008-marvis-alarm-handling` (R45). Commit `b571d2e7` sits on archive branch `archive/laptop-20261121/jmorrison-juniper-4008-marvis-alarm-isolation` (R68).
- The candidate commits `944a44846` and `ae3a6af8` add the record folder and the changelog fragment. They rename the two modules with zero changed lines. They modify the operation module by two lines, the actions docstring by two lines, five test modules by one to four lines each, the structure guard by eighteen lines, and the symbol guard by four lines. Commit `b571d2e7` removes the Marvis entry from the nested baseline (minus five lines) and changes one expected message line.
- The later candidate's module blobs equal the main blobs (R46 and R47). The move therefore changes no module content.

## Decisions

### D-1. Package layout and import path

- **Decision**: Move both modules into `alarm_handling/`. Export no symbol from `alarm_handling/__init__.py`. Keep no alias at an old path.
- **Alternatives**: Re-export the symbols from the package, which creates a second import path. Keep a compatibility module at the old path, which AGENTS forbids in its structure section (R92). The constitution also forbids wrapper functions (R78).
- **Chosen**: No re-export and no alias. Each caller imports the canonical module.
- **Reason**: The issue asks for canonical paths only. The searches found no import outside the listed rows (E-3).
- **Risk**: An importer outside the repository breaks. The repository holds none.

### D-2. Symbol preservation proof

- **Decision**: Add two `MODULE_PATHS` entries and rely on the rename-aware test. Do not rely on plain `symbol-diff` for the moved files.
- **Alternatives**: Plain `symbol-diff` per moved file, which cannot compare a renamed path (R96). A new guard file, which duplicates the existing rename-aware test.
- **Chosen**: The two `MODULE_PATHS` entries.
- **Reason**: Without an entry, `current_path` maps every path under `mist/` to the same path (R65). The old path then fails the `is_file` check (R21). The entries make the rename-aware test pass.
- **Risk**: The edit touches the file that PR #4208 holds (D-3).

### D-3. Held guard file

- **Decision**: Edit the held symbol guard file only after PR #4208 releases it or the coordinator issues a file-scoped handoff.
- **Alternatives**: Edit now and rebase later, which conflicts with the owner's pending work (R44). Ask the owner to add the two entries, which adds an owner dependency.
- **Chosen**: Wait for the release or the handoff.
- **Reason**: The issue comments hold the file for PR #4208 (R44 and R77). AGENTS requires a stop when a different agent owns the file.
- **Risk**: The serial slot waits for PR #4208.

### D-4. Nested ratchet update

- **Decision**: Remove the Marvis actions entry from `nested_package_baseline.json`, and change the expected message to `32 violations, 235 total excess`.
- **Alternatives**: Keep the entry, which the ratchet rejects as stale (R95). Lower the threshold, which weakens the guard.
- **Chosen**: Remove the entry and update the message.
- **Reason**: The current message expects 33 and 236 (R19). The entry holds six children (R18), and the move leaves five (R01, R04). The arithmetic is exact: 236 minus one equals 235, and 33 minus one equals 32.
- **Risk**: None beyond the expected message. The ratchet reads tracked files only, so the moved files must be staged first.

### D-5. Structure proof

- **Decision**: Add one guard test that checks the exact child sets of both packages.
- **Alternatives**: Rely on the nested ratchet, which counts only directories over the limit and does not check child names (R19 and the ratchet logic). Add a script outside the guards, which CI would not run.
- **Chosen**: One test in `test_src_domain_structure.py`, before line 120 (R66).
- **Reason**: The issue requires exact counts. Candidate commit `944a44846` (R69) already adds a test of this form.
- **Risk**: The test names the modules, so a future rename edits it.

### D-6. Touched debt

- **Decision**: Record the function-length and name-count debt in `plan.md`. Remediate it in a separate child issue under #3824.
- **Alternatives**: Split `_send_batches` and `apply` in this move. That adds behavior risk and breaks the blob equality that proves the move is a pure rename (R46 and R47). Ignore the debt, which the constitution forbids (R31).
- **Chosen**: Record the debt and file the child issue before publication.
- **Reason**: The constitution requires a recorded debt and a separate action for each touched violation (R31). Function lengths: `_send_batches` 28 lines, `apply` 29 lines, limit 25 (R88).
- **Risk**: The debt remains until the child issue merges.

### D-7. Changelog fragment

- **Decision**: Add `changelog.d/issue-4008-marvis-alarm-handling.md` with one heading and one `Changed` bullet.
- **Alternatives**: No fragment, under rule 4 of the changelog README (R34) and the user-visible wording of the copilot instructions (R36).
- **Chosen**: One fragment.
- **Reason**: The constitution says each change MUST add one fragment (R35). The guard `test_changelog_fragment_policy.py` checks the name form (R62).
- **Risk**: The governance text conflicts (analysis F-05). The release coordinator resolves the wording.

### D-8. Branch and commit names

- **Decision**: Branch `chore/4008-marvis-alarm-handling`. Commit subject and pull request title `refactor(marvis): isolate alarm handling modules`.
- **Alternatives**: A `refactor/` branch, which AGENTS does not list (R93). A `feat/` branch, which implies a feature.
- **Chosen**: `chore/` for the branch, `refactor` for the commit.
- **Reason**: AGENTS allows `feat`, `fix`, `chore`, or `docs` for the branch, and says the commit type can be more precise (R93). The pull request body must carry `Closes #4008` (R94).
- **Risk**: None.

### D-9. Fresh branch from current main

- **Decision**: Create a fresh branch from current main. Reuse the content by blob equality, not by rebasing the older candidate.
- **Alternatives**: Rebase commit `b571d2e7`, which starts 43 commits behind main (R68 and R69). Conflicts are likely in the held guard (R44) and in the test module that PR #4607 changed on main (R75). Cherry-pick `944a44846` and `b571d2e7`, which has the same conflicts.
- **Chosen**: Fresh branch and manual edits that match the verified candidate content.
- **Reason**: The candidate module blobs equal main (R46 and R47). The candidate edits are small, so a manual edit is cheap and reviewable.
- **Risk**: A manual edit can differ from the candidate. T-LOCAL-GATES checks the result.

### D-10. Logger names and class module paths

- **Decision**: Accept the new `__name__` logger names and the new class `__module__` values. Record them in the pull request body.
- **Alternatives**: Pin the old names as strings, which contradicts the `__name__` convention in both modules (R71 and R72) and keeps a stale name.
- **Chosen**: Accept and record the change.
- **Reason**: The focused test reads `alarms_module.__name__` (R67), so it follows the new name. The local search found no config or data key that names the old logger (E-3).
- **Risk**: An operator log filter that names the old logger stops matching. The repository holds no such filter.

### D-11. Gate scope

- **Decision**: Run every applicable local gate before the local commit. That includes the full test shards and the coverage run.
- **Alternatives**: Run only the focused gates named in the issue test plan. Rely on CI alone.
- **Chosen**: Every applicable gate.
- **Reason**: The constitution requires every existing gate that applies, and no step may be skipped (R80). The copilot instructions list the local gates (R27).
- **Risk**: The full run takes about 30 minutes.

### D-12. Menu references

- **Decision**: Regenerate the menu references with the CI forms, and keep each generated file only when its content changes.
- **Alternatives**: Edit the maps by hand, which drifts. Skip the regeneration, which CI rejects on drift (R61).
- **Chosen**: Run `python scripts/generate_menu_wiki.py`, then `python -m scripts.menu_api_map --check`.
- **Reason**: The interactive-safe map cites `client.py` for the alarm rows (R63), and no row names a moved module (E-14). The change therefore predicts no content change (U-5).
- **Risk**: The prediction fails if the generator reads the moved module names. T-LOCAL-GATES checks it.

## Remote verification

Each row is one remote or GitHub check. Blob SHA columns hold the Git blob SHA for a file, the tree SHA for a directory, or the text `commit object, no blob` for a commit check. Local SDK rows cite the installed package and carry the local `git hash-object` value. The result vocabulary is present, absent, partial, or stale. `partial` means the content exists on an archive branch and not on main.

| # | Claim | Path | Ref | Blob or tree SHA | Result | Line |
| - | - | - | - | - | - | - |
| R01 | The actions root holds six direct modules on main | `src/mist/intelligence/marvis/actions` | main | ff3a77de4c303606a12d231897e598df812ea6af | present | 0 |
| R02 | `acknowledgement.py` holds the acknowledger class | `src/mist/intelligence/marvis/actions/acknowledgement.py` | main | 765c01070ebdf0d79580af464441f9f44e3c34fb | present | 48 |
| R03 | `alarms.py` holds the alarm index class | `src/mist/intelligence/marvis/actions/alarms.py` | main | c61405c839212c6c64c5cbd8c07cd2e582cd4287 | present | 59 |
| R04 | The `alarm_handling` package is absent on main | `src/mist/intelligence/marvis/actions/alarm_handling/__init__.py` | main | absent on main | absent | 0 |
| R05 | `operation.py` imports the acknowledgement module | `src/mist/intelligence/marvis/actions/operation.py` | main | 4934903c7a2e81d225e75195779a7ba00bd634c9 | present | 51 |
| R06 | `operation.py` imports the alarms module | `src/mist/intelligence/marvis/actions/operation.py` | main | 4934903c7a2e81d225e75195779a7ba00bd634c9 | present | 57 |
| R07 | `operation.py` runs the alarm join in the export | `src/mist/intelligence/marvis/actions/operation.py` | main | 4934903c7a2e81d225e75195779a7ba00bd634c9 | present | 619 |
| R08 | `client.py` calls the SDK alarm search | `src/mist/intelligence/marvis/actions/client.py` | main | a7577ff0167e7462fb73adc39adc81036247cbdf | present | 251 |
| R09 | `client.py` calls the SDK acknowledge endpoint | `src/mist/intelligence/marvis/actions/client.py` | main | a7577ff0167e7462fb73adc39adc81036247cbdf | present | 202 |
| R10 | `test_acknowledgement.py` imports the acknowledgement module | `tests/unit/marvis/actions/test_acknowledgement.py` | main | 2faa094afe9c0680f7cf3e5d0efda5a4bed50111 | present | 7 |
| R11 | `test_acknowledgement.py` patches the module path three times | `tests/unit/marvis/actions/test_acknowledgement.py` | main | 2faa094afe9c0680f7cf3e5d0efda5a4bed50111 | present | 30 |
| R12 | `test_alarms.py` imports the alarms module object | `tests/unit/marvis/actions/test_alarms.py` | main | 59e0efa69a6ad97a3990fc09e7830285e15c0635 | present | 18 |
| R13 | `test_alarms.py` imports names from the alarms module | `tests/unit/marvis/actions/test_alarms.py` | main | 59e0efa69a6ad97a3990fc09e7830285e15c0635 | present | 19 |
| R14 | `test_operation.py` imports constants from the alarms module | `tests/unit/marvis/actions/test_operation.py` | main | be88636e3f63030d2dd73c8f10663e6fcacd7199 | present | 20 |
| R15 | `test_model.py` imports a constant from the alarms module | `tests/unit/marvis/actions/test_model.py` | main | 1abdc8f85a863751f603dd0219ccaecc8ead1ef9 | present | 15 |
| R16 | `test_properties.py` imports names from the alarms module | `tests/unit/marvis/actions/test_properties.py` | main | 66971a9907aa1cab8eec185c7526e9a0f9118b88 | present | 25 |
| R17 | The Marvis Actions doc names the old alarms path | `documentation/marvis-actions-api-endpoints.md` | main | 0e96ef07104c0d610c6d75dd558a0fd331499451 | present | 1329 |
| R18 | The nested baseline holds the Marvis actions entry | `tests/guardrails/nested_package_baseline.json` | main | 0d6c5ca933d83a4721c0bcc7220f69905fcf81f5 | present | 92 |
| R19 | The nested ratchet expects 33 violations and 236 excess | `tests/guardrails/test_nested_package_structure.py` | main | 5678277a376271483a6d340751e4c8ff7b5d92a3 | present | 177 |
| R20 | The symbol guard holds no mapping for the two alarm modules | `tests/guardrails/test_src_public_symbol_preservation.py` | main | 08f978e755abdf643e7a6d826811401f710883f8 | absent | 36 |
| R21 | The symbol guard holds the rename-aware module test | `tests/guardrails/test_src_public_symbol_preservation.py` | main | 08f978e755abdf643e7a6d826811401f710883f8 | present | 348 |
| R22 | The structure guard holds no `alarm_handling` test | `tests/guardrails/test_src_domain_structure.py` | main | 8c1567e3b78c57a9a7a40578106d4a34659a977a | absent | 0 |
| R23 | `MYPY_PATHS` includes the `src/` tree | `.github/workflows/ci.yml` | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 93 |
| R24 | `VULTURE_PATHS` includes the `src/` tree | `.github/workflows/ci.yml` | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 101 |
| R25 | `PYDOCSTYLE_PATHS` includes the `src/` tree | `.github/workflows/ci.yml` | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 104 |
| R26 | `INTERROGATE_PATHS` includes the `src/` tree | `.github/workflows/ci.yml` | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 107 |
| R27 | The copilot instructions hold the local gates section | `.github/copilot-instructions.md` | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 50 |
| R28 | The nested source package row names `test_move_module_guidance.py` | `.github/copilot-instructions.md` | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 259 |
| R29 | The move-a-module table names the guardrail and symbol gates | `.github/copilot-instructions.md` | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 261 |
| R30 | The copilot instructions require Python 3.15 or newer | `.github/copilot-instructions.md` | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 20 |
| R31 | The constitution defines the Five-Item Rule | `.specify/memory/constitution.md` | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 38 |
| R32 | The constitution states a mistapi 0.59 floor | `.specify/memory/constitution.md` | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 279 |
| R33 | The route function computes base-5 segments | `.specify/scripts/powershell/spec-route.ps1` | main | 37293a255f9b5de20ccb2b3ef0ad15717bab2826 | present | 4 |
| R34 | The changelog rule names the issue fragment form | `changelog.d/README.md` | main | fcbde10e0c293390bd9df8d62a5d61f158eca384 | present | 27 |
| R35 | The constitution requires one fragment for each change | `.specify/memory/constitution.md` | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 409 |
| R36 | The copilot instructions limit the fragment rule to user-visible changes | `.github/copilot-instructions.md` | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 451 |
| R37 | The OpenAPI alarm search path exists | `documentation/mist-api-openapi31yaml.yaml` | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 5330 |
| R38 | The OpenAPI alarm acknowledge path exists with `ackOrgMultipleAlarms` | `documentation/mist-api-openapi31yaml.yaml` | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 5226 |
| R39 | The OpenAPI `alarm_ids` schema holds no maximum item count | `documentation/mist-api-openapi31yaml.yaml` | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | absent | 68519 |
| R40 | The reference record exists on main | `specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv/spec.md` | main | 83b950279e45704943ad6942d23c8fc99cced492 | present | 1 |
| R41 | The route folder for issue 4008 is absent on main | `specs/numbered/0/0/1/1/2/0/1/3` | main | absent on main | absent | 0 |
| R42 | No folder with the issue prefix exists under `specs` on main | `specs` | main | absent on main | absent | 0 |
| R43 | The historical 3339 plan cites the old alarms path | `specs/3339-marvis-alarm-join/plan.md` | main | 2a255f592d59f2c450c3537540b16823e533ef77 | present | 87 |
| R44 | PR #4208 is open and changes the symbol guard file | `tests/guardrails/test_src_public_symbol_preservation.py` | main | 08f978e755abdf643e7a6d826811401f710883f8 | present | 0 |
| R45 | The preserved commit `ae3a6af8` heads an archive branch and is not on main | commit `ae3a6af8f7d29df15913879dd891987454716235` | ae3a6af8f7d29df15913879dd891987454716235 | commit object, no blob | partial | 0 |
| R46 | The later candidate `alarms.py` blob equals the main blob | `src/mist/intelligence/marvis/actions/alarm_handling/alarms.py` | b571d2e719034009f32786390dc5c88daea98566 | c61405c839212c6c64c5cbd8c07cd2e582cd4287 | partial | 0 |
| R47 | The later candidate `acknowledgement.py` blob equals the main blob | `src/mist/intelligence/marvis/actions/alarm_handling/acknowledgement.py` | b571d2e719034009f32786390dc5c88daea98566 | 765c01070ebdf0d79580af464441f9f44e3c34fb | partial | 0 |
| R48 | The legacy record folder exists on the archive branch | `specs/numbered/0/0/1/1/2/0/1/3/4008-marvis-alarm-handling/spec.md` | b571d2e719034009f32786390dc5c88daea98566 | f9dc9e2b1bd01f25e670ef1620e40ccdffe285b5 | present | 1 |
| R49 | The legacy spec names the bare issue slug as its branch | `specs/numbered/0/0/1/1/2/0/1/3/4008-marvis-alarm-handling/spec.md` | b571d2e719034009f32786390dc5c88daea98566 | f9dc9e2b1bd01f25e670ef1620e40ccdffe285b5 | stale | 3 |
| R50 | The legacy plan states Python 3.13 or newer | `specs/numbered/0/0/1/1/2/0/1/3/4008-marvis-alarm-handling/plan.md` | b571d2e719034009f32786390dc5c88daea98566 | 9faa5f8781c82d7de670283382a7d42a0779cb0b | stale | 14 |
| R51 | The legacy plan states that logger names stay unchanged | `specs/numbered/0/0/1/1/2/0/1/3/4008-marvis-alarm-handling/plan.md` | b571d2e719034009f32786390dc5c88daea98566 | 9faa5f8781c82d7de670283382a7d42a0779cb0b | stale | 30 |
| R52 | The legacy plan states that the actions package already holds five children | `specs/numbered/0/0/1/1/2/0/1/3/4008-marvis-alarm-handling/plan.md` | b571d2e719034009f32786390dc5c88daea98566 | 9faa5f8781c82d7de670283382a7d42a0779cb0b | absent | 26 |
| R53 | The legacy plan states that required gates ran before the commit | `specs/numbered/0/0/1/1/2/0/1/3/4008-marvis-alarm-handling/plan.md` | b571d2e719034009f32786390dc5c88daea98566 | 9faa5f8781c82d7de670283382a7d42a0779cb0b | absent | 29 |
| R54 | The legacy plan limits the change to three routed specification files | `specs/numbered/0/0/1/1/2/0/1/3/4008-marvis-alarm-handling/plan.md` | b571d2e719034009f32786390dc5c88daea98566 | 9faa5f8781c82d7de670283382a7d42a0779cb0b | stale | 36 |
| R55 | The legacy tasks instruct a `git mv` move | `specs/numbered/0/0/1/1/2/0/1/3/4008-marvis-alarm-handling/tasks.md` | b571d2e719034009f32786390dc5c88daea98566 | 4c17b5e12336d1138c096af7c8f6851d3876838f | present | 11 |
| R56 | The legacy changelog fragment uses a bare `Changed` heading | `changelog.d/issue-4008-marvis-alarm-handling.md` | b571d2e719034009f32786390dc5c88daea98566 | a5c766fd3829b637b1294f27ee1b494666214122 | stale | 1 |
| R57 | The legacy tasks name the closing keyword | `specs/numbered/0/0/1/1/2/0/1/3/4008-marvis-alarm-handling/tasks.md` | b571d2e719034009f32786390dc5c88daea98566 | 4c17b5e12336d1138c096af7c8f6851d3876838f | present | 16 |
| R58 | The SDK search function exists in the installed package | `.venv\Lib\site-packages\mistapi\api\v1\orgs\alarms.py` | local-venv | 5eca8df601ae5d366a7443d9b2a2effe76ccc094 | present | 135 |
| R59 | The SDK acknowledge function exists in the installed package | `.venv\Lib\site-packages\mistapi\api\v1\orgs\alarms.py` | local-venv | 5eca8df601ae5d366a7443d9b2a2effe76ccc094 | present | 17 |
| R60 | The installed `mistapi` is version 0.64.1 | `.venv\Lib\site-packages\mistapi-0.64.1.dist-info` | local-venv | directory, no blob | present | 0 |
| R61 | The menu drift job names the check form of the menu map command | `documentation/quality-gates.md` | main | 6776d334cca5d9b43273473a06da367a65605c6d | present | 67 |
| R62 | The changelog fragment guard exists | `tests/guardrails/test_changelog_fragment_policy.py` | main | dbd5e8776797f12536b3bc2bd613143b85f3fc4a | present | 0 |
| R63 | The interactive-safe map row for the acknowledge endpoint cites the client module | `documentation/menu-api/interactive-safe.md` | main | 57b580ddc1c4b9fe4971c72fb26a592764e7ac53 | present | 1879 |
| R64 | The route parent `specs/numbered/0/0/1/1` holds five children, and the route reuses child `2` | `specs/numbered/0/0/1/1` | main | 473ee2af5aae152de6b3522e8920b62cbfa92508 | present | 0 |
| R65 | `current_path` returns the same path for an unmapped canonical root | `tests/guardrails/test_src_public_symbol_preservation.py` | main | 08f978e755abdf643e7a6d826811401f710883f8 | present | 295 |
| R66 | The structure guard holds the canonical source path test | `tests/guardrails/test_src_domain_structure.py` | main | 8c1567e3b78c57a9a7a40578106d4a34659a977a | present | 120 |
| R67 | The join logs test reads the module logger name | `tests/unit/marvis/actions/test_alarms.py` | main | 59e0efa69a6ad97a3990fc09e7830285e15c0635 | present | 302 |
| R68 | The later candidate commit `b571d2e7` sits on an archive branch and is not on main | commit `b571d2e719034009f32786390dc5c88daea98566` | b571d2e719034009f32786390dc5c88daea98566 | commit object, no blob | partial | 0 |
| R69 | Commit `944a44846` is an ancestor of `b571d2e7` and is not on main | commit `944a44846cc315543d2d20665b05da16074fa620` | 944a44846cc315543d2d20665b05da16074fa620 | commit object, no blob | partial | 0 |
| R70 | The actions package docstring names the five modules and the alarm modules | `src/mist/intelligence/marvis/actions/__init__.py` | main | c1667510431eb7a73d925d211fb1bd93fca5bb97 | present | 4 |
| R71 | `acknowledgement.py` creates its logger from `__name__` | `src/mist/intelligence/marvis/actions/acknowledgement.py` | main | 765c01070ebdf0d79580af464441f9f44e3c34fb | present | 30 |
| R72 | `alarms.py` creates its logger from `__name__` | `src/mist/intelligence/marvis/actions/alarms.py` | main | c61405c839212c6c64c5cbd8c07cd2e582cd4287 | present | 43 |
| R73 | The batch-size comment cites a 1,000 alarm ID document limit | `src/mist/intelligence/marvis/actions/acknowledgement.py` | main | 765c01070ebdf0d79580af464441f9f44e3c34fb | present | 32 |
| R74 | PR #4557 is merged and changes the nested baseline and the symbol guard file | commit `e2e7413bba32ce0f733e18dae903f031ff8102f6` | e2e7413bba32ce0f733e18dae903f031ff8102f6 | commit object, no blob | present | 0 |
| R75 | PR #4607 is merged and changes two Marvis action test modules | commit `b9ef5f3a11af8d8436d384c4e854c3e0b529aafe` | b9ef5f3a11af8d8436d384c4e854c3e0b529aafe | commit object, no blob | present | 0 |
| R76 | A link from PR #4372 to issue #4008 is absent | PR #4372 (merged 2026-10-20) | PR #4372 | no link found | absent | 0 |
| R77 | Among seven open pull requests, only PR #4208 overlaps the candidate file set | open pull requests | main | gh pr list files | present | 0 |
| R78 | Constitution Principle II forbids standalone wrapper functions | `.specify/memory/constitution.md` | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 91 |
| R79 | Constitution Principle III requires safe input and typed confirmation | `.specify/memory/constitution.md` | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 113 |
| R80 | Constitution Principle IV requires the full deployment pipeline | `.specify/memory/constitution.md` | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 143 |
| R81 | Constitution Principle V requires ASCII-only log output | `.specify/memory/constitution.md` | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 182 |
| R82 | Constitution Principle VI requires inline comments | `.specify/memory/constitution.md` | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 204 |
| R83 | Constitution Principle VII requires action logging | `.specify/memory/constitution.md` | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 235 |
| R84 | The constitution technology section names mistapi as the sole REST interface | `.specify/memory/constitution.md` | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 274 |
| R85 | The constitution container section names Podman | `.specify/memory/constitution.md` | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 300 |
| R86 | The constitution test-container rule names the compose group | `.specify/memory/constitution.md` | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 302 |
| R87 | The constitution data directory rule names `data/` for product outputs | `.specify/memory/constitution.md` | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 326 |
| R88 | The constitution function limits set 25 lines per function | `.specify/memory/constitution.md` | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 85 |
| R89 | The constitution audience standard requires junior NOC wording | `.specify/memory/constitution.md` | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 414 |
| R90 | The constitution escalation rule requires a spec for three or more files | `.specify/memory/constitution.md` | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 420 |
| R91 | The constitution multi-agent section governs branches and worktrees | `.specify/memory/constitution.md` | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 453 |
| R92 | AGENTS requires five children or fewer at each structure level | `AGENTS.md` | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 77 |
| R93 | AGENTS requires a branch type of `feat`, `fix`, `chore`, or `docs` | `AGENTS.md` | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 194 |
| R94 | AGENTS requires `Closes #<issue>` in the pull request body | `AGENTS.md` | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 224 |
| R95 | The nested guard rejects a stale baseline entry | `tests/guardrails/test_nested_package_structure.py` | main | 5678277a376271483a6d340751e4c8ff7b5d92a3 | present | 137 |
| R96 | The PR #4607 body states that plain `symbol-diff` cannot compare a renamed path | PR #4607 body | b9ef5f3a11af8d8436d384c4e854c3e0b529aafe | PR body text, no blob | present | 0 |
| R97 | `acknowledgement.py` takes the API client in its constructor | `src/mist/intelligence/marvis/actions/acknowledgement.py` | main | 765c01070ebdf0d79580af464441f9f44e3c34fb | present | 51 |
| R98 | `alarms.py` takes the API client in the alarm join constructor | `src/mist/intelligence/marvis/actions/alarms.py` | main | c61405c839212c6c64c5cbd8c07cd2e582cd4287 | present | 164 |

## Legacy record check

The archive record at commit `b571d2e7` holds three files and one changelog fragment. The brief requires this check before reuse. Only the folder name and two process claims are reused. The content is not reused.

| L | Archive claim | Result | Row | Reason |
| - | - | - | - | - |
| L1 | Folder `4008-marvis-alarm-handling` sits under the route | present | R48 | The folder name matches the route in E-8. |
| L2 | The feature branch is `4008-marvis-alarm-handling` | stale | R49 | AGENTS requires a type prefix (R93). |
| L3 | The plan states Python 3.13 or newer | stale | R50 | The copilot instructions require Python 3.15 (R30). |
| L4 | The plan states that logger names stay unchanged | stale | R51 | Both modules use `__name__` (R71 and R72). The names change. |
| L5 | The plan states that the actions package already holds five children | absent | R52 | The main tree still holds six children (R01). |
| L6 | The plan states that required gates ran before the commit | absent | R53 | The archive holds no gate output. This research ran no gate. |
| L7 | The plan limits the change to three routed specification files | stale | R54 | The brief, section 4, requires spec, plan, tasks, analysis, and design. The archive holds three of them. |
| L8 | The tasks instruct a `git mv` move | present | R55 | The candidate renames show zero changed lines (R46 and R47). |
| L9 | The changelog fragment uses a bare `Changed` heading | stale | R56 | The changelog README requires a heading that names the change (R34). |
| L10 | The tasks name the closing keyword | present | R57 | AGENTS requires the keyword in the body (R94). |

Totals for the existing record: verified 3 (L1, L8, L10), stale 5 (L2, L3, L4, L7, L9), absent 2 (L5, L6).

## Local evidence

Local facts come from the shared checkout. Local evidence proves nothing about GitHub. The remote rows above carry every claim about code on main.

- **E-1**: Local `HEAD` and `origin/main` both equal `f03c6c9b36d612a48d7b9652998c2fd87dd777ca`. Read with `git rev-parse`.
- **E-2**: The shared checkout holds five unrelated modified files: `src/foundation/support/utils/logger_utils.py`, `src/interfaces/wan_performance/collection/request_admission.py`, `src/mist/intelligence/reports/subscription_expiry/client.py`, `tests/unit/marvis/mist/intelligence/reports/audits/credentials/subscription_expiry/test_client.py`, and `tests/unit/wan_dashboard/wan_performance/collection/test_request_admission.py`. Read with `git status --porcelain` and no optional locks.
- **E-3**: A local search for the old module paths found 12 active lines and 2 historical lines. Active lines: `operation.py` lines 51 and 57. `test_acknowledgement.py` lines 7, 30, 43, and 58. `test_alarms.py` lines 18 and 19. `test_operation.py` line 20. `test_model.py` line 15. `test_properties.py` line 25. The documentation line is 1329. Historical lines: `specs/3339-marvis-alarm-join/plan.md` line 87 and `tasks.md` line 24. Two other files import unchanged modules: `MistHelper.py` line 777 and `web_portal/services/operation.py` line 639. The search found no logger-name string, no config, and no stored key that names an old path.
- **E-4**: The local actions directory holds `__init__.py`, `acknowledgement.py`, `alarms.py`, `client.py`, `model.py`, `operation.py`, `selection.py`, and an untracked `__pycache__` folder. The structure guard excludes `__pycache__`.
- **E-5**: Test function counts by a line search for `def test_`: `test_acknowledgement.py` 3, `test_alarms.py` 32, `test_model.py` 56, `test_operation.py` 65, `test_properties.py` 16, `test_src_domain_structure.py` 4, `test_src_public_symbol_preservation.py` 20, `test_nested_package_structure.py` 9, `test_move_module_guidance.py` 7, and `test_marvis_actions_portal_exposure.py` 10. The sum is 222. The new structure test adds one, so the focused selection holds 223.
- **E-6**: Function and name counts. `acknowledgement.py` holds 6 functions, including `__init__`, and 7 top-level names. `alarms.py` holds 10 functions and 6 top-level names. `operation.py` holds 25 top-level names. Top-level names are classes, functions, and module-level assignments. Imports are excluded.
- **E-7**: A search for non-ASCII characters found zero lines in `acknowledgement.py` and zero lines in `alarms.py`.
- **E-8**: Route computation. The base-5 digits of 4008 are `0,0,1,1,2,0,1,3`, which produce the route `0\0\1\1\2\0\1\3`. The function `Get-SpecRadixSegments` (R33) computes the digits at eight-digit width. Parent counts are in R64. Each parent holds five children or fewer, and the route adds one new child only at depth eight.
- **E-9**: Local `git hash-object` values equal the remote blob SHAs for `acknowledgement.py`, `alarms.py`, `operation.py`, `client.py`, `nested_package_baseline.json`, `test_nested_package_structure.py`, `test_src_public_symbol_preservation.py`, `ci.yml`, `marvis-actions-api-endpoints.md`, and `changelog.d/README.md`. Remote line numbers therefore apply to the local copies.
- **E-10**: The installed `mistapi` module `alarms.py` has the local `git hash-object` value `5eca8df601ae5d366a7443d9b2a2effe76ccc094`. The file is outside the repository tree.
- **E-11**: Local line numbers for the alarm calls. `operation.py` line 503 constructs the acknowledger, line 619 calls the join in the export, and line 708 calls the join in another mode. `client.py` line 145 defines the alarm search method, line 191 defines the acknowledge method, line 202 calls the SDK acknowledge function, line 248 defines the first alarm page reader, and line 251 calls the SDK search function.
- **E-12**: No local folder under `specs` has a name that starts with `4008-`.
- **E-13**: Git lists `remotes/origin/archive/laptop-20261121/jmorrison-juniper-refactor-4008-marvis-alarm-handling` as the branch that contains commit `ae3a6af8`.
- **E-14**: A read of the remote interactive-safe menu map found zero lines that name the moved module paths. Line 1879 names the client module.

## Unverified

- **U-1**: The comment at `acknowledgement.py` line 32 states that the bundled Mist API document limits each batch to 1,000 alarm IDs (R73). The acknowledge description (R38) and the `alarm_ids` schema (R39) hold no such limit. The JSON twin of the OpenAPI file was not searched. The batch size stays in the code and the comment stays unchanged.
- **U-2**: The candidate issue comments report test counts: 284 tests with one skip, 267 tests, 273 tests, a 42-failure guardrail run, and 41 route-contract failures. This research ran no test, so these counts stay unverified.
- **U-3**: The 41 PowerShell route-contract failures appear only when `pwsh` is absent. This session has PowerShell 7.6, so the claim may not hold here. The claim stays unverified.
- **U-4**: Lint, format, type, security, and quality results after the move. This research ran no lint, type, or build command. T-LOCAL-GATES records these results.
- **U-5**: The regenerated menu maps stay unchanged. The generator was not run. The prediction rests on R63 and E-14.
- **U-6**: The limit of five operations per statement block. No local gate reports this limit, so the research did not count it.
- **U-7**: The state of main at publication. Main moves over time. T-PR repeats the remote checks before the push.
