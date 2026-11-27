# Quickstart: Unit test domain packages

These steps reproduce the baseline of this record and verify each batch. Run the steps in the repository checkout after the bootstrap in `.github/copilot-instructions.md`. Do not run the collection step during record authoring.

## Prerequisites

Set the GitHub variables before each `gh` call. Do not print their values.

```powershell
$env:GH_HOST='github.com'
$env:GH_TOKEN=$env:COPILOT_GH_ACCOUNT_github_2E_com_jmorrison_2D_juniper
```

## 1. Count The Root On Main

Run this read-only command. The baseline count is 50. The final count is 5.

```powershell
gh api 'repos/jmorrison-juniper/MistHelper/git/trees/main?recursive=1' --jq '[.tree[]|select(.path|startswith("tests/unit/"))|.path|split("/")|.[2]]|unique|length'
```

## 2. List The Tracked Root Names Locally

Use tracked names only. Untracked local directories do not count.

```powershell
git -C 'C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper' ls-files -- tests/unit | ForEach-Object { ($_ -split '/')[2] } | Sort-Object -Unique
```

## 3. Count Oversized Grouping Directories On Main

Run this read-only command after each batch. The output lists each directory with more than five children.

```powershell
gh api 'repos/jmorrison-juniper/MistHelper/git/trees/main?recursive=1' --jq '[.tree[]|select(.path|startswith("tests/unit/"))|.path] as $p | [$p[]|split("/")|.[0:-1]|join("/")] | group_by(.) | map({d: .[0], n: length}) | map(select(.n > 5)) | .[] | "\(.n) \(.d)"'
```

## 4. Check Open Holds

Run this read-only command before each batch. It lists the open pull requests that touch a `tests/` path.

```powershell
gh pr list -R jmorrison-juniper/MistHelper --state open --json number,title,isDraft,files --jq '.[] | {number, title, isDraft, owned: [.files[].path | select(startswith("tests/"))]} | select(.owned|length>0) | "#\(.number) draft=\(.isDraft) \(.title) :: \(.owned|length)"'
```

## 5. Capture The Collection Baseline

Run this once before the first move. The output file is git-ignored evidence under `test-artifacts/`.

```powershell
New-Item -ItemType Directory -Force -Path 'test-artifacts\4142' | Out-Null
python -B -m pytest -p no:cacheprovider --collect-only -q tests/unit > test-artifacts\4142\baseline-node-ids.txt
```

## 6. Verify A Batch

Run the focused tests for each moved directory. Then run the guards and the collection parity check.

```powershell
python -m pytest tests/unit/marvis/mist/intelligence/analytics
python -m pytest tests/guardrails
python -B -m pytest -p no:cacheprovider --collect-only -q tests/unit > test-artifacts\4142\after-node-ids.txt
```

Compare the two node-ID files. The after file must contain every line of the baseline after the path normalization of the moved paths.

## 7. Scan For Old Paths

Replace the path with each old path that the batch moves. The command must return no active reference.

```powershell
git grep -n "tests/unit/upgrade_portal" HEAD -- ':(exclude)specs' ':(exclude)CHANGELOG.md'
```

## 8. Check The Production Diff

This command must return no file for a test-only batch.

```powershell
git diff --name-only origin/main -- src web_portal Dockerfile Containerfile
```

## 9. Run The Local Gates

Run each gate that applies to the changed files. These commands follow the local gates table in `.github/copilot-instructions.md`.

```powershell
python -m ruff check .
python -m black --check .
python -m pytest tests/guardrails/local_test_quality_loop/test_guidance.py::TestLiveGuides
test-quality-analyzer --gate --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json
```

## 10. Check The Final Layout

After the final batch, the root count from step 1 is 5. Each directory in step 3 has five children or fewer. The collection parity check in step 6 passes.
