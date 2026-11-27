# Research: Early dependency check without half-removed packages

## Method

- Remote truth: GitHub `main`, read with `gh api` and `gh` read commands. The tree call returned 11,404 entries with `truncated=False`. A second tree call counted the children of route parents.
- Local checkout: HEAD `f03c6c9b36d612a48d7b9652998c2fd87dd777ca` on branch `main`. Local evidence supports a claim only when the blob SHA matches `main`.
- Blob match: `git hash-object` (no `-w`) gave the same blob SHA as `main` for `src/foundation/runtime/bootstrap/dependency_check.py` (514d1fb2), `src/foundation/runtime/bootstrap/package_installer.py` (aff48cba), `MistHelper.py` (98d78284), `src/foundation/support/refactors/package_import_map.py` (383bf9ba), and `requirements.txt` (50fe63d4). For these files, a local line number equals the remote line number.
- Line numbers in the table come from decoded `main` content, or from the blob match above.
- Legacy record: a search of `specs\` found no folder whose name starts with `4930-`. A glob search and a PowerShell search agreed, so the record starts without a legacy folder.

## Issue Facts

- Issue #4930 is open. It was created on 2026-11-25 at 17:11:12 UTC, and it has no comments. Its labels are `bug` and `MistHelper.py`.
- Context (issue text): the early check runs when `MistHelper.py` starts. Without `DISABLE_AUTO_INSTALL=true`, it imports each requirement to probe it. It then upgrades the packages that do not match their pin in the same process.
- Reproduction (issue text, live run of 2026-11-24, `DISABLE_AUTO_INSTALL` unset): the log shows `Attempting to upgrade 20 outdated dependencies`. Eleven upgrades worked, and nine failed after the uv try and the pip fallback. Five packages (`numpy`, `pydantic_core`, `simplejson`, `charset_normalizer`, `wcwidth`) kept a dist-info folder with no RECORD file and with missing files.
- Error text (issue text): `ImportError: cannot import name 'JSONDecodeError' from 'simplejson'` on each later start. A locked `ruff.exe` stopped one `uv sync` during its uninstall step.
- Expected results (issue text), mapped to the spec: the check does not change a loaded package (FR-001, FR-002). A failed upgrade restores the old package or leaves it untouched (FR-004). The check refuses an environment that differs from the lock by many packages, and it says `Run uv sync --locked --extra dev` (FR-005, FR-006).
- Workaround (issue text): set `DISABLE_AUTO_INSTALL=true`. Repair the environment with `uv sync --locked --extra dev` after each process that runs from it stops (FR-010 for the documentation).

## Current Behavior (verified on main)

- The startup path calls `_MH.early_dependency_check()` (R-10). That function builds `DependencyCheckOrchestrator` with the import map (R-11, R-12) and calls `run()` (R-13).
- The missing check calls `_is_importable`, which runs `__import__` on each requirement (R-14, R-15). Each probe loads the module into the process.
- An outdated package is upgraded with uv, then with pip (R-16). The header text is `Attempting to upgrade %s outdated dependencies...` (R-18).
- The import map lists 11 pip names (blob match, `package_import_map.py`). It has no key for `charset-normalizer` (R-23). Without a mapping, the code uses the pin name as the import name (`dependency_check.py` line 167, blob match). Unverified item 4 covers the failed import that follows.
- The installed version comes from `importlib.metadata.version` (R-28). The PyPI lookup imports `requests` in-process (R-27). The auto-upgrade flag defaults to `true` in `MistHelper.py` (`AUTO_UPGRADE_DEPENDENCIES`, local line 1360, blob 98d78284).
- `requirements.txt` is an export from `uv export --locked` (R-26). It pins each package with `==` (R-24, R-25).
- The legacy upgrade method `_upgrade_all_dependencies` has one definition and no call site in `MistHelper.py` (R-29). The remote code search found no call in `src/`. The search index does not cover `MistHelper.py`, because the file is large, so R-29 depends on the blob match.
- The installer exposes `install_with_uv` and `install_with_pip` (R-21, R-22). It has no stage-and-swap operation.
- The bootstrap runs the locked sync with `uv sync --locked --extra dev` (R-35).
- CI jobs run on `ubuntu-latest`. All 27 runner labels in `ci.yml` name `ubuntu-latest`, and none names Windows or macOS (R-44).
- The container files set `DISABLE_AUTO_INSTALL=true` (R-42, R-43).

## Decisions

### D-1 Read presence and version from metadata, not from imports

- Alternatives: (a) keep `__import__` and skip loaded packages. (b) Use `importlib.util.find_spec` with the import map. (c) Probe each package in a child Python process.
- Chosen: `importlib.metadata` for the version, and a RECORD check for completeness.
- Reason: The probe loads every package (R-14). Option (a) would block every repair, because the probe loads each package before the repair step. Option (b) needs the import map, and the map lacks hyphenated pins (R-23). Option (c) adds one interpreter start for each package on each launch.
- Risk: A package with intact metadata and broken code passes the probe. The operator sees the error at first use, and the repair command fixes it.

### D-2 Skip loaded packages, and treat an unmapped package as loaded

- Alternatives: (a) skip only the packages that the probe loaded. (b) Disable in-process changes for upgrades.
- Chosen: skip a package when any top-level name from `importlib.metadata.packages_distributions()` is a key in `sys.modules`. Treat a package with no top-level name as loaded.
- Reason: Other startup code can load a package. The PyPI lookup imports `requests` (R-27). Option (a) misses these loads. Option (b) removes a feature that the expected results of the issue keep.
- Risk: The Python documentation states that `packages_distributions()` is not reliable for some editable installs (see Sources). The rule to treat an unmapped package as loaded keeps those packages unchanged.

### D-3 Refuse a run with more than five drifted packages

- Alternatives: refuse above zero packages. Refuse above ten packages.
- Chosen: five.
- Reason: Five keeps the in-process change for a small pin change. The failed run in issue #4930 reported 20 outdated packages. Ten allows more locked-file risk for each run. Zero stops the feature for a one-package drift.
- Risk: A fresh environment with more than five missing packages now stops and names the repair command. The bootstrap already runs the locked sync (R-35). The operator runs the repair command.

### D-4 Snapshot RECORD files before each upgrade, and restore after a failed upgrade

- Alternatives: (a) reinstall the old version from the uv cache. (b) install the new version into a staging folder, then swap it. (c) prevent the failure only, with no restore.
- Chosen: snapshot and restore.
- Reason: The snapshot needs no network and no installer support. Option (a) needs the old wheel in the cache. Option (b) needs a stage-and-swap operation, and the installer does not expose one (R-21, R-22). Option (c) cannot meet the expected result for a failure that the check does not predict.
- Risk: The snapshot uses disk space equal to the RECORD files of the upgraded package. A restore can fail for a file that another process holds. New files that the failed upgrade wrote remain in place. The check logs the snapshot path, so the operator can repair the environment.

### D-5 Use the requirements.txt pins as the lock reference, with a test against uv.lock

- Alternatives: parse `uv.lock` at runtime with `tomllib`.
- Chosen: `requirements.txt`, which the early check already parses. TC-13 checks the pins against `uv.lock` at test time.
- Reason: The header states that `uv export --locked` writes the file (R-26). Runtime parsing of `uv.lock` (about 450 KB in the local checkout) adds a second parser and extra I/O on each start.
- Risk: A stale export. TC-13 detects a difference during tests.

### D-6 Remove the import map field from the orchestrator

- Alternatives: keep an unused field. Delete `package_import_map.py`.
- Chosen: remove the field, and its one lookup and call site. Keep the module and `PackageImportMapManager.MAPPING`.
- Reason: An unused field misleads a reader. Deleting the module widens the diff. A later issue can remove the module.
- Risk: A test or a caller that reads the field fails. T010 updates the known callers.

### D-7 Keep the PyPI latest-version lookup and its requests import

- Alternatives: (a) use `urllib.request` for the lookup. (b) disable the lookup by default.
- Chosen: keep the lookup unchanged.
- Reason: Option (a) creates a Bandit finding for `urlopen`, and the local gate allows no finding at any severity (the Local gates table, R-45). Option (b) changes the product default, and the issue does not request it.
- Risk: The lookup loads more packages in-process, and the loaded-package skip covers those packages (D-2).

### D-8 Verify Windows locking with fake-based tests and a manual check

- Alternatives: (a) add a Windows runner to CI. (b) write a pytest case that loads a real native module on Windows.
- Chosen: fake-based tests in CI, and a manual Windows check in `design/quickstart.md`.
- Reason: CI runs on `ubuntu-latest` only (R-44). A Windows runner adds minutes to every pull request. Option (b) needs a Windows fixture in CI.
- Risk: A Windows regression appears only in the manual check.

## Remote Verification

Each row is one check. The table has 52 rows. `remote_checks` in `META_DIR\4930-STATUS.json` holds the same 52 rows in the same order.

| ID | Claim | Path | Ref | Blob SHA | Result | Line |
| - | - | - | - | - | - | - |
| R-01 | Issue 4930 is open with labels bug and MistHelper.py | gh issue view 4930 | main | none | present | 0 |
| R-02 | No open pull request touches the target files | gh pr list --state open | main | none | present | 0 |
| R-03 | No record exists under the route folder | specs/numbered/0/0/1/2/4/2/1/0/ | main | none | absent | 0 |
| R-04 | Route parent holds five children | specs/numbered/0/0/1/2 | main | none | present | 0 |
| R-05 | Route parent holds one child before this record | specs/numbered/0/0/1/2/4/2/1 | main | none | present | 0 |
| R-06 | Bootstrap folder holds five children | src/foundation/runtime/bootstrap | main | none | present | 0 |
| R-07 | changelog.d holds 335 children | changelog.d | main | none | present | 0 |
| R-08 | Route script sets base 5 and an eight-segment width | .specify/scripts/powershell/spec-route.ps1 | main | 37293a255f9b5de20ccb2b3ef0ad15717bab2826 | present | 17 |
| R-09 | Constitution version is 1.9.0 | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 4 |
| R-10 | Startup calls the early check | src/foundation/support/refactors/main_entrypoint.py | main | 1402beb8e9a901a5ef143c43cc32a8bcad6f8fb1 | present | 258 |
| R-11 | Entry point constructs the orchestrator with the import map | MistHelper.py | main | 98d7828479ded6bc4c83d15e0c1847171cfbfd49 | present | 1051 |
| R-12 | Entry point passes the import map argument | MistHelper.py | main | 98d7828479ded6bc4c83d15e0c1847171cfbfd49 | present | 1055 |
| R-13 | Entry point calls orchestrator.run() | MistHelper.py | main | 98d7828479ded6bc4c83d15e0c1847171cfbfd49 | present | 1063 |
| R-14 | Import probe calls __import__ on each requirement | src/foundation/runtime/bootstrap/dependency_check.py | main | 514d1fb2efaf778ca51edf03e8df550e81efc09c | present | 178 |
| R-15 | Missing check calls the import probe | src/foundation/runtime/bootstrap/dependency_check.py | main | 514d1fb2efaf778ca51edf03e8df550e81efc09c | present | 170 |
| R-16 | Upgrade path tries uv before pip | src/foundation/runtime/bootstrap/dependency_check.py | main | 514d1fb2efaf778ca51edf03e8df550e81efc09c | present | 298 |
| R-17 | Orchestrator declares the import map field | src/foundation/runtime/bootstrap/dependency_check.py | main | 514d1fb2efaf778ca51edf03e8df550e81efc09c | present | 72 |
| R-18 | Upgrade header text is Attempting to upgrade | src/foundation/runtime/bootstrap/dependency_check.py | main | 514d1fb2efaf778ca51edf03e8df550e81efc09c | present | 50 |
| R-19 | Orchestrator class holds 22 methods, starting at run | src/foundation/runtime/bootstrap/dependency_check.py | main | 514d1fb2efaf778ca51edf03e8df550e81efc09c | present | 80 |
| R-20 | Local blob equals remote blob for dependency_check.py | src/foundation/runtime/bootstrap/dependency_check.py | main | 514d1fb2efaf778ca51edf03e8df550e81efc09c | present | 0 |
| R-21 | Installer exposes install_with_uv | src/foundation/runtime/bootstrap/package_installer.py | main | aff48cba3dc1a91654f165b9c9c9871286a0db03 | present | 63 |
| R-22 | Installer exposes install_with_pip | src/foundation/runtime/bootstrap/package_installer.py | main | aff48cba3dc1a91654f165b9c9c9871286a0db03 | present | 73 |
| R-23 | Import map has no charset-normalizer key | src/foundation/support/refactors/package_import_map.py | main | 383bf9ba7c403789151b2cb25428416e6fb81b0f | absent | 25 |
| R-24 | Lock reference pins charset-normalizer 3.5.2 | requirements.txt | main | 50fe63d4cf5e6071612c62c288e965190c60b969 | present | 23 |
| R-25 | Lock reference pins mistapi 0.64.1 | requirements.txt | main | 50fe63d4cf5e6071612c62c288e965190c60b969 | present | 129 |
| R-26 | Lock reference header states uv export --locked | requirements.txt | main | 50fe63d4cf5e6071612c62c288e965190c60b969 | present | 2 |
| R-27 | PyPI lookup imports requests in-process | MistHelper.py | main | 98d7828479ded6bc4c83d15e0c1847171cfbfd49 | present | 983 |
| R-28 | Installed version reads importlib.metadata | MistHelper.py | main | 98d7828479ded6bc4c83d15e0c1847171cfbfd49 | present | 941 |
| R-29 | Legacy upgrade method has no call site | MistHelper.py | main | 98d7828479ded6bc4c83d15e0c1847171cfbfd49 | present | 1687 |
| R-30 | pyproject mistapi floor is 0.64.1 | pyproject.toml | main | eca34c826ea44ba4f2faefc07d04c2c117e99751 | present | 29 |
| R-31 | Instruction file names mistapi floor 0.64.0 | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | stale | 21 |
| R-32 | pyproject requires Python 3.15 or newer | pyproject.toml | main | eca34c826ea44ba4f2faefc07d04c2c117e99751 | present | 23 |
| R-33 | Dev extra lists uv 0.13.9 | pyproject.toml | main | eca34c826ea44ba4f2faefc07d04c2c117e99751 | present | 101 |
| R-34 | uv.lock exists at the root | uv.lock | main | 5445b4eb382dc9f6dd5c351ba40c521f01f93165 | present | 0 |
| R-35 | Locked sync test asserts the repair argument vector | tests/unit/config/foundation/runtime/startup/bootstrap/dependency/test_uv_locked_sync.py | main | 678632eec13c5673cbc453210d47a09bacf8b431 | present | 44 |
| R-36 | Venv guard test patches _is_importable | tests/bootstrap/test_dependency_check_venv_guard.py | main | fa65751e2fd94fa7b11c04e99c7cc63f930a46ff | present | 102 |
| R-37 | Path test class covers the import probe | tests/unit/config/foundation/runtime/startup/bootstrap/dependency/test_dependency_check_paths.py | main | 5393612abe72a8d708a5e704a8cfeb55da3206f7 | present | 333 |
| R-38 | Constructor test passes an import map | tests/unit/config/standalone/foundation/runtime/startup/test_dependency_check.py | main | 7192e79f77799f77d368dd43180a561902f7271a | present | 30 |
| R-39 | Operator guide has no repair or DISABLE_AUTO_INSTALL text | documentation/operator-guide.md | main | 60d28f9ea461fc8798973d1d1b7e40491c27c248 | absent | 0 |
| R-40 | Development setup has no repair or DISABLE_AUTO_INSTALL text | documentation/development-setup.md | main | 1733975a7e0a0962fe5367e165a21f5831f8c3e5 | absent | 0 |
| R-41 | README has the Documentation section | README.md | main | 331a4567f72156fe2a3e3ee91005d2cbbcaed6d0 | present | 115 |
| R-42 | Containerfile sets DISABLE_AUTO_INSTALL=true | Containerfile | main | bc9249a19f6f181e7ea0e2c4b565a139d16d9253 | present | 166 |
| R-43 | Dockerfile sets DISABLE_AUTO_INSTALL=true | Dockerfile | main | bc9249a19f6f181e7ea0e2c4b565a139d16d9253 | present | 166 |
| R-44 | All 27 CI runner labels are ubuntu-latest | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 142 |
| R-45 | Local gates table starts at the Local gates heading | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 50 |
| R-46 | Fragment names follow the pr and issue patterns | changelog.d/README.md | main | fcbde10e0c293390bd9df8d62a5d61f158eca384 | present | 26 |
| R-47 | Reference record spec exists | specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv/spec.md | main | 83b950279e45704943ad6942d23c8fc99cced492 | present | 0 |
| R-48 | Feature 1020 spec exists | specs/1020-safe-test-clean-run/spec.md | main | 72d3e94f4ecf3339f7a9304c573f88a74b76e9e3 | present | 0 |
| R-49 | Issue 1020 is an unrelated Mist API issue | gh issue view 1020 | main | none | present | 0 |
| R-50 | Related issues share the early-check topic by title | gh issue list search | main | none | present | 0 |
| R-51 | Pull request template exists | .github/PULL_REQUEST_TEMPLATE.md | main | ed03e8f36f20962d9c7bbd74cde192d5adfdcc77 | present | 0 |
| R-52 | AGENTS.md exists at the root | AGENTS.md | main | 44a9affffb5bd6f774973a845d27343e4e528b6ad | present | 0 |

Result values: `present` means the claim holds on `main`. `absent` means the named item does not exist on `main`. `stale` means the claim contradicts `main`.

Route check: 4930 in base 5 is `124210`. Padded to eight segments, it is `00124210`, which gives `0/0/1/2/4/2/1/0`. This equals ROUTE, and the formula appears at R-08. The route parents hold five or fewer children (R-04, R-05).

Related pull requests and issues:
- Pull request 4924 is merged on 2026-11-26. It delivers the reference record for issue 4920. It is not linked to issue 4930.
- Pull request 95 is merged on 2026-04-08. It matches issue number 4930 only through a black release note that cites psf/black#4930. It is unrelated.
- Issue 1020 is an unrelated Mist API issue. The folder `specs/1020-safe-test-clean-run` is a feature number, not an issue number. The folder added the interpreter gate that this change keeps (FR-008).
- Related by title: issue 1701 (closed, import-time side effects in the bootstrap).
- Related by title: issue 4774 (open, locked bootstrap with a pip mirror).
- Related by title: issue 4591 (open, locked worktree bootstrap metadata).
- Related by title: issue 4879 (open, development setup text). It owns `documentation/development-setup.md`.

## Mist API and mistapi

Not applicable. The change calls no Mist endpoint. The mistapi pin appears only as a version constraint in `pyproject.toml` (R-30) and `requirements.txt` (R-25). The OpenAPI file and the SDK source are outside the scope of this change.

## Skills

No skill was loaded. No listed skill covers the Python bootstrap, the Windows file lock, or the uv command.

## Sources

Local paths:
- `AGENTS.md`, `.github/copilot-instructions.md`, `.specify/memory/constitution.md`, and the four templates under `.specify/templates/`.
- `specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv/` (the reference record, for shape only).
- `src/foundation/runtime/bootstrap/dependency_check.py`, `package_installer.py`, and `uv_runtime.py`.
- `MistHelper.py` lines 938 to 1063 and line 1360 (blob 98d78284).
- `src/foundation/support/refactors/package_import_map.py` and `main_entrypoint.py`.
- The test files named in the Remote Verification table.

URLs:
- Python `importlib.metadata`, read on the official documentation site: https://docs.python.org/3/library/importlib.metadata.html. The sections "Distribution files" and "Mapping import to distribution packages" describe these facts. The function `files()` returns `None` when the RECORD metadata is missing. The function `packages_distributions()` was added in Python 3.10. The mapping is not reliable for some editable installs.
- Microsoft `CreateFileW`, read on Microsoft Learn: https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-createfilew. The `dwShareMode` description states that a delete request fails when an open handle lacks `FILE_SHARE_DELETE`, and that `ERROR_SHARING_VIOLATION` reports the conflict.
- Microsoft `DeleteFileW`, read on Microsoft Learn: https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-deletefilew. The page describes `ERROR_ACCESS_DENIED` for read-only files. It does not describe loaded modules.

## Unverified

1. The live run log of 2026-11-24 in the issue body. The log is not in the repository. The claim rests on the issue text.
2. Five packages (numpy, pydantic_core, simplejson, charset_normalizer, wcwidth) left with a dist-info folder and no RECORD file. This state depends on one machine. This task is read-only, so the state cannot be reproduced here.
3. The Windows loader keeps a handle on a loaded `.pyd` file without `FILE_SHARE_DELETE`. The cited Microsoft pages state the share rule, but they do not state the share mode of the loader.
4. An import of a hyphenated name, such as `charset-normalizer`, fails. This follows from the import rules of Python. The change does not run the import.
5. The `charset-normalizer` wheel ships compiled extension modules on Windows. No file in the repository or the wheel was read.
6. `requests` imports `charset_normalizer` in-process. The file `requirements.txt` has one `# via requests` annotation, which sits under `certifi` (line 18). The annotation does not show the dependency edge for `charset-normalizer`. The edge is outside the repository.
7. `ruff.exe` held by the editor stopped a `uv sync` (issue evidence). The repository does not show this event.
8. A loaded module keeps its file locked for the life of the process on Windows. The loader behavior is not verified (item 3).
