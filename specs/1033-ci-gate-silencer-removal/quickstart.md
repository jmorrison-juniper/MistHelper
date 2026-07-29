# Quickstart: Verify the CI Gate Silencer Removal

**Feature**: `1033-ci-gate-silencer-removal` | **Branch**: `ci/891-893-gate-silencers` | **Date**: 2026-07-28

This guide validates the three gate changes. Two gates prove themselves on the workstation. The third gate proves itself only in CI.

Run every step in order. Do not push until step 3 passes.

---

## Prerequisites

| Item | Value |
| - | - |
| Working directory | The repository root. |
| Branch | `ci/891-893-gate-silencers`. Do not create a branch and do not switch branches. |
| Python interpreter | `.venv\Scripts\python.exe`. The global `python` on this machine is broken. |
| GitHub CLI | `gh auth status` must report an authenticated account with read access to code scanning. |

Confirm the branch before any edit.

```powershell
git branch --show-current   # must print ci/891-893-gate-silencers
```

---

## Step 1: Verify the pylint gate

This step proves requirement FR-006 and success criterion SC-002.

```powershell
.venv\Scripts\python.exe -m pylint src/ --fail-under=9.5
"exit=$LASTEXITCODE"
```

| Check | Expected result |
| - | - |
| Exit code | 0 |
| Message count | About 1259. A small drift is acceptable when the pylint version differs. |
| Score line | At or above 9.5 out of 10. |

Confirm that the three previously hidden packages now report messages. This proves success criterion SC-001.

```powershell
.venv\Scripts\python.exe -m pylint src/ --fail-under=9.5 2>&1 |
  Select-String -Pattern 'src\\maps|src\\ssh|src\\ui' |
  Measure-Object -Line
```

Each of the three paths must return at least one line.

---

## Step 2: Verify the vulture gate

This step proves requirement FR-008 and success criterion SC-004.

```powershell
.venv\Scripts\python.exe -m vulture src/ --min-confidence 70
"exit=$LASTEXITCODE"
```

| Check | Expected result |
| - | - |
| Exit code | 0 |
| Finding count | 0 |

Re-measure the cliff when a reviewer asks for the evidence behind the choice of 70.

```powershell
$c90 = (.venv\Scripts\python.exe -m vulture src/ --min-confidence 90 2>&1 | Measure-Object -Line).Lines
$c70 = (.venv\Scripts\python.exe -m vulture src/ --min-confidence 70 2>&1 | Measure-Object -Line).Lines
$c60 = (.venv\Scripts\python.exe -m vulture src/ --min-confidence 60 2>&1 | Measure-Object -Line).Lines
"conf90=$c90 conf70=$c70 conf60=$c60"   # expect conf90=0 conf70=0 conf60=306
```

---

## Step 3: Verify that both configuration files still parse

A broken YAML file stops every gate and produces no evidence. Check both files before the push.

```powershell
.venv\Scripts\python.exe -c "import yaml; yaml.safe_load(open('.github/workflows/ci.yml')); yaml.safe_load(open('.github/codeql/codeql-config.yml')); print('yaml ok')"
```

Confirm that no `'90'` survives for the vulture setting. Research decision R2 explains why two sites exist.

```powershell
Select-String -Path ".github\workflows\ci.yml" -Pattern "vulture-confidence|VULTURE_CONFIDENCE" -Context 0,2
```

Both results must show `70`.

Confirm that the pylint ignore flag is gone.

```powershell
Select-String -Path ".github\workflows\ci.yml" -Pattern "--ignore=maps"   # must return nothing
```

---

## Step 4: Push once and open the pull request

A push to this branch starts no workflow. Both workflows trigger on a pull request against `main`. The pull request is the only path to a CodeQL result.

```powershell
git add .github/workflows/ci.yml .github/codeql/codeql-config.yml CHANGELOG.md specs/1033-ci-gate-silencer-removal
git commit -m "ci: remove the pylint, vulture, and CodeQL gate silencers (#891, #892, #893)"
git push origin ci/891-893-gate-silencers
gh pr create --base main --head ci/891-893-gate-silencers --fill-first
```

Watch the gate results.

```powershell
gh pr checks --watch
```

| Job | Expected result |
| - | - |
| Pylint (score gate) | Pass, inside 10 minutes. |
| Vulture (dead code) | Pass, inside 5 minutes. |
| CodeQL Analysis | Complete. The alert count is the evidence, not the pass state. |

---

## Step 5: Read the CodeQL result

Set the reference once.

```powershell
$repo = "jmorrison-juniper/MistHelper"
$ref  = "refs/heads/ci/891-893-gate-silencers"
```

Count the alerts for each query.

```powershell
gh api "repos/$repo/code-scanning/alerts?ref=$ref&per_page=100" `
  --jq '[.[] | select(.rule.id == "py/stack-trace-exposure")] | length'

gh api "repos/$repo/code-scanning/alerts?ref=$ref&per_page=100" `
  --jq '[.[] | select(.rule.id == "py/clear-text-logging-sensitive-data")] | length'
```

Record both counts in the pull request body. Requirement FR-014 states this rule.

---

## Step 6: Confirm that each query actually ran

Research decision R7 states the reason for this step. A count of zero is ambiguous on its own. It can mean a clean result, or it can mean a query that the default suite never executed. The two meanings lead to opposite conclusions.

Find the analysis identifier for the branch.

```powershell
gh api "repos/$repo/code-scanning/analyses?ref=$ref&per_page=5" --jq '.[0].id'
```

Download the SARIF report for that analysis and list the rule identifiers that the run carried.

```powershell
$analysisId = gh api "repos/$repo/code-scanning/analyses?ref=$ref&per_page=5" --jq '.[0].id'
gh api "repos/$repo/code-scanning/analyses/$analysisId" -H "Accept: application/sarif+json" > "$env:TEMP\codeql_1033.sarif"

.venv\Scripts\python.exe -c "import json;d=json.load(open(r'$env:TEMP\codeql_1033.sarif'));ids={r['id'] for e in d['runs'][0]['tool'].get('extensions',[]) for r in e.get('rules',[])}|{r['id'] for r in d['runs'][0]['tool']['driver'].get('rules',[])};print('stack-trace-exposure ran:','py/stack-trace-exposure' in ids);print('clear-text-logging ran:','py/clear-text-logging-sensitive-data' in ids)"
```

| Output | Meaning | Verdict |
| - | - | - |
| `True` and the alert count is 0 | The query ran and found nothing. | `clean` |
| `True` and the alert count is above 0 | The query ran and found something. | `false_positive` or `real`, after the team judges the alerts. |
| `False` | The default suite never ran the query. The exclusion was always inert. | `inert` |

---

## Step 7: Apply the decision for each query

[data-model.md](data-model.md) holds the full decision table. The two queries are independent. One may end in `removed` while the other ends in `restored`.

| Verdict | Action |
| - | - |
| `clean` | Keep the removal. Record the count and the run link in the pull request. |
| `inert` | Keep the removal. Note in the pull request that the exclusion never had an effect. |
| `false_positive` | Restore that one exclusion. Write a Review Record with the three facts. |
| `real`, a fix fits this feature | Keep the removal. Land the fix in this pull request. |
| `real`, a fix does not fit | Restore that one exclusion with a Review Record. Open a follow-up issue and link it. |

A restored exclusion follows the format in [contracts/review-comment.md](contracts/review-comment.md). Push the restoration as a second commit on the same pull request.

Re-run the check after any second commit.

```powershell
gh pr checks --watch
```

---

## Step 8: Close the record

| Task | Requirement |
| - | - |
| Open a follow-up issue for the 502 newly visible pylint messages and link it from the pull request. | FR-020 |
| Record the vulture confidence 60 slice against issue #1703. | FR-021 |
| Fill the CodeQL counts into the changelog entry under `## [Unreleased]`. | FR-019 |
| Confirm that `.github/codeql/codeql-config.yml` holds no undefended exclusion. | FR-017 |

Run the Simplified Technical English linter on every changed prose file.

```powershell
.venv\Scripts\python.exe -m tools.ste_linter "CHANGELOG.md"
.venv\Scripts\python.exe -m tools.ste_linter "specs\1033-ci-gate-silencer-removal\plan.md"
```

Each file must score 80 or above.

---

## Acceptance checklist

The feature is complete when every line below is true.

- [ ] `.github/workflows/ci.yml` holds no `--ignore` flag on the pylint step.
- [ ] The pylint job passes in CI and the log names `src/maps`, `src/ssh`, and `src/ui`.
- [ ] Both `vulture-confidence` values in `.github/workflows/ci.yml` read `'70'`.
- [ ] The vulture job passes in CI with 0 findings.
- [ ] The pylint step and the vulture step each carry a comment with the three required facts.
- [ ] The pull request records a finding count for each of the two CodeQL queries.
- [ ] Every exclusion that survives in `.github/codeql/codeql-config.yml` carries a Review Record.
- [ ] No surviving rationale claims that the tool never logs an actual secret.
- [ ] `CHANGELOG.md` holds one entry under `## [Unreleased]` that names issues #891, #892, and #893.
- [ ] The pull request links the follow-up issue for the 502 pylint messages.
- [ ] The pull request states the grouping reason for the three issues.
- [ ] Every changed prose file scores 80 or above on the Simplified Technical English linter.
- [ ] The full CI suite is green on the branch.
