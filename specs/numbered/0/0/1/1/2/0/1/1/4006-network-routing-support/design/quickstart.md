# Quickstart: Isolate Network Routing Support Modules

## Setup

Set the repository path once in each PowerShell session. Activate the environment.

```powershell
$repo = 'C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper'
Set-Location -LiteralPath $repo
.venv\Scripts\Activate.ps1
```

Run these two lines before each `gh` command. They select the GitHub host and the account token. Do not print the token value.

```powershell
$env:GH_HOST = 'github.com'
$env:GH_TOKEN = $env:COPILOT_GH_ACCOUNT_github_2E_com_jmorrison_2D_juniper
```

## Reproduce the Current State

Run these commands before the change. Each command shows the baseline that the change alters.

Step 1. List the network root. The output shows seven entries and no `support` folder.

```powershell
Get-ChildItem -LiteralPath (Join-Path $repo 'src\mist\networking\network') | Select-Object Name
```

Step 2. Find old-path references in active files. The output shows references in seven files.

```powershell
git -C $repo grep -n -F -e "network._routing_utils_display" -e "network/_routing_utils_display" -e "network._routing_utils_parsing" -e "network/_routing_utils_parsing" -e "network._routing_utils_payload" -e "network/_routing_utils_payload" -- src tests scripts documentation README.md
```

Step 3. Run the nested-package ratchet. The test passes before the change.

```powershell
python -m pytest tests/guardrails/test_nested_package_structure.py -q
```

## Verify the Change

Each block names one test case (TC). Run the commands in order.

TC-01. Structure guard (FR-003, FR-004, FR-016). Expect all tests to pass.

```powershell
python -m pytest tests/guardrails/test_network_routing_support_structure.py -q
```

TC-02. Routing unit tests (FR-007, FR-008, FR-018). Expect zero failures.

```powershell
python -m pytest tests/unit/test_routing_utils.py -q
```

TC-03. Unparseable-response guards (FR-008, FR-018). Expect zero failures.

```powershell
python -m pytest tests/unit/test_unparseable_response_guards.py -q
```

TC-04. Symbol preservation guard (FR-011). Expect zero failures.

```powershell
python -m pytest tests/guardrails/test_src_public_symbol_preservation.py -q
```

TC-05. Performance catalog guard (FR-013, FR-014). Expect zero failures.

```powershell
python -m pytest tests/guardrails/test_performance_hook_catalog.py -q
```

TC-06. Nested-package ratchet (FR-015). Expect zero failures and the report `32 violations, 234 total excess`.

```powershell
python -m pytest tests/guardrails/test_nested_package_structure.py -q
```

TC-07. Move-module guidance guard (FR-020). Expect zero failures.

```powershell
python -m pytest tests/guardrails/test_move_module_guidance.py -q
```

TC-08. Import smoke (FR-002, FR-006). The first command exits with code 0. The second command fails with `ModuleNotFoundError`.

```powershell
python -c "import src.mist.networking.network.support._routing_utils_payload"
python -c "import src.mist.networking.network._routing_utils_payload"
```

TC-09. Old-path and logger scan (FR-006, FR-009, FR-010, FR-013). The first command prints nothing. The second command prints nothing, because the record folder is excluded.

```powershell
git -C $repo grep -n -F -e "network._routing_utils_display" -e "network/_routing_utils_display" -e "network._routing_utils_parsing" -e "network/_routing_utils_parsing" -e "network._routing_utils_payload" -e "network/_routing_utils_payload" -- src tests scripts documentation README.md ':(exclude)tests/guardrails/test_performance_hook_catalog.py'
git -C $repo diff --name-only origin/main -- specs ':(exclude)specs/numbered/0/0/1/1/2/0/1/1/4006-network-routing-support'
```

TC-10. Menu regeneration stability (FR-012). Run both generators, then check status. Expect no changed file under `documentation`.

```powershell
python scripts/generate_menu_wiki.py
python -m scripts.menu_api_map
git -C $repo status --short -- documentation
```

TC-11. Blob identity for moved files (FR-001, FR-018). Expect the three blobs in the order listed.

```powershell
git -C $repo hash-object src\mist\networking\network\support\_routing_utils_display.py
git -C $repo hash-object src\mist\networking\network\support\_routing_utils_parsing.py
git -C $repo hash-object src\mist\networking\network\support\_routing_utils_payload.py
```

Expected blobs: `81619905f517792de24025d65b267bc540c158b8`, `50cd37ff14e40e0b8f1ddda896ac3a9c1ab82f86`, and `38c2458ff14370be660d956ca30c252dc4fd291c`.

TC-12. Tracked changelog fragment and record (FR-017, FR-022). Expect both paths listed after the commit.

```powershell
git -C $repo ls-files changelog.d/issue-4006-network-routing-support.md specs/numbered/0/0/1/1/2/0/1/1/4006-network-routing-support
```

TC-13. Publication gate (FR-021). Expect no output. Any listed pull request holds a file in this set.

```powershell
gh pr list -R jmorrison-juniper/MistHelper --state open --json number,title,isDraft,files --jq '.[] | select([.files[].path | test("test_src_public_symbol_preservation|test_routing_utils|nested_package_baseline|test_performance_hook_catalog|menu-api/websocket|Menu-API-Endpoints-Websocket")] | any) | "#\(.number) draft=\(.isDraft) \(.title)"'
```

TC-14. Symbol diff (FR-011, FR-020). Expect `no module-level name changed` and exit code 0 for each moved file.

```powershell
symbol-diff --base origin/main src\mist\networking\network\support\_routing_utils_display.py
symbol-diff --base origin/main src\mist\networking\network\support\_routing_utils_parsing.py
symbol-diff --base origin/main src\mist\networking\network\support\_routing_utils_payload.py
```

TC-15. Diff review for credentials, calls, and messages (FR-019). Review each added line. Expect no new network call, credential read, or message change.

```powershell
git -C $repo diff -M --stat origin/main
git -C $repo diff -M origin/main -- src
```

TC-16. Worktree and label check (FR-021). Expect the branch worktree in the list and `in-progress` in the labels.

```powershell
git -C $repo worktree list
gh issue view 4006 -R jmorrison-juniper/MistHelper --json labels --jq '[.labels[].name] | join(",")'
```

## Final Gates

Run each command from the local gates table in `.github/copilot-instructions.md` that applies to the changed files. The commands below use the paths from `.github/workflows/ci.yml` (lines 93, 101, 104, and 107).

```powershell
python -m py_compile MistHelper.py
python -m ruff check .
python -m black --check .
python -m mypy src/ MistHelper.py wsgi.py scripts/mist_ideas_analyzer_pkg/__init__.py scripts/mist_ideas_distiller_v2_pkg/__init__.py --config-file pyproject.toml
python -m pytest tests --ignore=tests/e2e --cov=src --cov-report=
radon cc src\mist\networking\network -j | complexity-gate --max 10
bandit -c pyproject.toml -r src\mist\networking\network -q
pylint src/ --fail-under=9.5
vulture src/ MistHelper.py wsgi.py web_portal --min-confidence 70
pydocstyle src/ wsgi.py web_portal
interrogate src/ MistHelper.py wsgi.py wsgi_capture.py web_portal --fail-under 90
symbol-diff --base origin/main src\mist\networking\network\routing_utils.py
ste-linter --config .ste-linter.toml --min-score 80 changelog.d\issue-4006-network-routing-support.md documentation\menu-api\websocket.md documentation\wiki\Menu-API-Endpoints-Websocket.md
```

The `--test` sweep and the two full-suite shard commands run in CI. Run them on the local machine when time allows.

```powershell
python MistHelper.py --test
pytest-chunks -x --chunk-timeout 900 --test-timeout 120 tests\unit --split tests\unit\upgrade_portal
pytest-chunks -x --chunk-timeout 900 --test-timeout 120 tests\contract tests\guardrails tests\integration --split tests\contract\upgrade_portal --split tests\integration\upgrade_portal
```

The test-quality ratchet runs after the commit. Its preflight and gate commands come from the section "Test quality ratchet" of `.github/copilot-instructions.md`.

```powershell
$BASE_REF = "main"
python -B -m pytest -p no:cacheprovider -s -q tests/guardrails/local_test_quality_loop/test_guidance.py::TestLiveGuides
test-quality-analyzer --gate --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json --changed-from "origin/$BASE_REF" --full-gate-path .github/workflows/ci.yml --full-gate-path requirements-dev.txt
```
