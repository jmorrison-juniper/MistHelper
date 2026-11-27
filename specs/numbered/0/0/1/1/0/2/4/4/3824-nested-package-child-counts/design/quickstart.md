# Quickstart: Nested Source Package Child Counts

Run these commands from the repository root. Each command is read-only, except the test runs that write to their own caches. Before each `gh` command, set the host and the token as the orchestrator requires. Never print the token value.

## Step 1: Confirm the measured base

```powershell
$env:GH_HOST='github.com'
$env:GH_TOKEN=$env:COPILOT_GH_ACCOUNT_github_2E_com_jmorrison_2D_juniper
gh api repos/jmorrison-juniper/MistHelper/git/ref/heads/main --jq .object.sha
```

Expected result: `f03c6c9b36d612a48d7b9652998c2fd87dd777ca`.

## Step 2: Run the guard

```powershell
python -m pytest tests/guardrails/test_nested_package_structure.py -s -q
```

Expected result on the measured base: the printed line `nested_package_scope: 190 directories examined, 33 violations, 236 total excess`.

## Step 3: Recount the remote tree

```powershell
$env:GH_HOST='github.com'
$env:GH_TOKEN=$env:COPILOT_GH_ACCOUNT_github_2E_com_jmorrison_2D_juniper
gh api "repos/jmorrison-juniper/MistHelper/git/trees/main?recursive=1" --jq '[.tree[] | select(.type == "blob" and (.path | startswith("src/")) and (.path | endswith(".py"))) | .path | split("/") as $p | ([range(1; ($p | length) - 1) | [($p[:.] | join("/")), $p[.]]] + [[($p[:-1] | join("/")), $p[-1]]]) | .[]] | unique | group_by(.[0]) | map({dir: .[0][0], count: (map(.[1] | if endswith(".py") then (if . == "__init__.py" then 0 else 1 end) else 1 end) | add)}) | map(select(.dir != "src")) | {dirs_examined: length, violations: (map(select(.count > 5)) | length), total_excess: (map(select(.count > 5) | .count - 5) | add)}'
```

Expected result on the measured base: `"dirs_examined":190`, `"violations":33`, and `"total_excess":236`.

## Step 4: Confirm that a destination is free

```powershell
git -C "C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper" ls-files -- src/mist/access/response_integrity.py
```

Expected result before W1-05: no output.

## Step 5: Find the consumers of an old path

```powershell
git -C "C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper" grep -n "mist.access.api.response_integrity" -- src tests scripts documentation README.md MistHelper.py
```

Use the output to update each consumer in the same slice.

## Step 6: Run the slice gates

Run the gates in `checklists\slice-gates.md` that apply to the changed files. Start with these commands:

```powershell
python -m pytest tests/guardrails
python -m ruff check .
python -m black --check .
python -m mypy src/ MistHelper.py wsgi.py scripts/mist_ideas_analyzer_pkg/__init__.py scripts/mist_ideas_distiller_v2_pkg/__init__.py --config-file pyproject.toml
```

The mypy path list matches the `MYPY_PATHS` value in `.github/workflows/ci.yml`, line 93.

## Step 7: Confirm the guard gate row

```powershell
python -m pytest tests/guardrails/test_move_module_guidance.py
```

After task T004, the nested source package row also names `python -m pytest tests/guardrails/test_nested_package_structure.py`.
