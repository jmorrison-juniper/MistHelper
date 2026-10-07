# Quickstart: Validate the Phase-Watch Wording

## Prerequisites

Run the worktree bootstrap once:

```powershell
python scripts/bootstrap_worktree.py
```

Run all commands from the repository root. Use the worktree branch
`jmorrison-juniper-docs-3332-phase-watch-boundary`.

## 1. Confirm the Implementation Manifest

The implementation can change only these files:

```text
src/interfaces/portals/upgrade_portal/upgrade/driver.py
src/interfaces/portals/upgrade_portal/upgrade/org_cascade/walk.py
src/interfaces/portals/upgrade_portal/app/assets/templates/partials/org_phase_list.html
tests/contract/upgrade_portal/test_org_phase_watch_contract.py
tests/unit/upgrade_portal/test_org_phase_list_parity.py
changelog.d/issue-3332-phase-watch-wording.md
```

Spec Kit records can also exist under this feature directory.

## 2. Run the Exact-String Audit Across `tests/`

Run this audit before the edit:

```powershell
$oldPromise = "A phase starts only after the phase before it reports settled."
Get-ChildItem tests -Recurse -File |
    Select-String -SimpleMatch $oldPromise
```

Run this audit after the edit:

```powershell
$requiredStrings = @(
    "The phase watch starts after the portal sends the upgrade requests."
    "It observes the submitted work and sends no firmware request."
    "It does not prove that the cloud accepted each request or that the portal sent device types in this order."
    "Warning: If a submission result is uncertain, do not start another upgrade. A second upgrade can target the same devices."
)
$testFiles = Get-ChildItem tests -Recurse -File
foreach ($requiredString in $requiredStrings) {
    $matches = $testFiles | Select-String -SimpleMatch $requiredString
    if (-not $matches) {
        throw "The test tree does not assert the required string: $requiredString"
    }
    $allowedTests = @(
        "*tests\contract\upgrade_portal\test_org_phase_watch_contract.py"
        "*tests\unit\upgrade_portal\test_org_phase_list_parity.py"
    )
    $unexpected = $matches | Where-Object {
        $path = $_.Path
        -not ($allowedTests | Where-Object { $path -like $_ })
    }
    if ($unexpected) {
        throw "An unapproved test owns the phase-watch wording: $($unexpected.Path)"
    }
}
```

Expected result: The contract test and the parity test assert the approved
multi-site wording. No other test defines different wording.

## 3. Confirm the Direct Contract Assertion

Review
`tests/contract/upgrade_portal/test_org_phase_watch_contract.py`.

Confirm that one test renders the organization operation page. Confirm that it
directly asserts each literal string from
[phase-watch-wording.md](contracts/phase-watch-wording.md).

Run the smallest test boundary:

```powershell
python -m pytest `
    tests\contract\upgrade_portal\test_org_phase_watch_contract.py `
    tests\unit\upgrade_portal\test_org_phase_list_parity.py -q
```

Expected result: All tests pass.

## 4. Run the Complete Upgrade Portal Browser Suite

Strict mode prevents a missing browser from becoming a successful skipped run.
Use one free test port from the repository range.

```powershell
$env:UPGRADE_PORTAL_E2E_STRICT = "1"
$env:CAPTURE_PORT = "9606"
python -m pytest tests\e2e\upgrade_portal -v --timeout=180
```

Expected result: The complete `tests/e2e/upgrade_portal` suite passes with no
browser skip.

## 5. Run the Applicable Repository Gates

Run the Python syntax checks:

```powershell
python -m py_compile `
    src\interfaces\portals\upgrade_portal\upgrade\driver.py `
    src\interfaces\portals\upgrade_portal\upgrade\org_cascade\walk.py `
    tests\contract\upgrade_portal\test_org_phase_watch_contract.py
```

Run lint and format checks:

```powershell
python -m ruff check `
    src\interfaces\portals\upgrade_portal\upgrade\driver.py `
    src\interfaces\portals\upgrade_portal\upgrade\org_cascade\walk.py `
    tests\contract\upgrade_portal\test_org_phase_watch_contract.py
python -m black --check `
    src\interfaces\portals\upgrade_portal\upgrade\driver.py `
    src\interfaces\portals\upgrade_portal\upgrade\org_cascade\walk.py `
    tests\contract\upgrade_portal\test_org_phase_watch_contract.py
```

Run the repository type gate:

```powershell
$mypyPaths = "src/ MistHelper.py wsgi.py scripts/mist_ideas_analyzer_pkg/__init__.py scripts/mist_ideas_distiller_v2_pkg/__init__.py"
python -m mypy $mypyPaths --config-file pyproject.toml
```

Run the docstring and security gates:

```powershell
python -m pydocstyle src\interfaces\portals\upgrade_portal\upgrade\driver.py `
    src\interfaces\portals\upgrade_portal\upgrade\org_cascade\walk.py
python -m interrogate src\interfaces\portals\upgrade_portal --fail-under 90
python -m bandit -c pyproject.toml -r src\interfaces\portals\upgrade_portal -q
```

Run the release-note guard:

```powershell
python -m pytest tests\guardrails\test_changelog_fragment_policy.py -q
```

Run the test-quality preflight before the commit:

```powershell
python -B -m pytest -p no:cacheprovider -s -q `
    tests\guardrails\local_test_quality_loop\test_guidance.py::TestLiveGuides
```

Run the STE check for the feature records and fragment:

```powershell
ste-linter --config .ste-linter.toml --min-score 80 `
    specs\numbered\0\0\1\0\1\3\1\2\3332-phase-watch-submission-boundary\spec.md `
    specs\numbered\0\0\1\0\1\3\1\2\3332-phase-watch-submission-boundary\plan.md `
    specs\numbered\0\0\1\0\1\3\1\2\3332-phase-watch-submission-boundary\research.md `
    specs\numbered\0\0\1\0\1\3\1\2\3332-phase-watch-submission-boundary\data-model.md `
    specs\numbered\0\0\1\0\1\3\1\2\3332-phase-watch-submission-boundary\quickstart.md `
    specs\numbered\0\0\1\0\1\3\1\2\3332-phase-watch-submission-boundary\contracts\phase-watch-wording.md `
    changelog.d\issue-3332-phase-watch-wording.md
```

## 6. Verify the Wording-Only Diff

```powershell
git diff --check
git diff --word-diff=porcelain origin/main...HEAD -- `
    src\interfaces\portals\upgrade_portal\upgrade\driver.py `
    src\interfaces\portals\upgrade_portal\upgrade\org_cascade\walk.py `
    src\interfaces\portals\upgrade_portal\app\assets\templates\partials\org_phase_list.html `
    tests\contract\upgrade_portal\test_org_phase_watch_contract.py `
    changelog.d\issue-3332-phase-watch-wording.md
```

Confirm that the diff changes wording and direct assertions only.

Search the diff for excluded subjects:

```powershell
git diff origin/main...HEAD -- |
    Select-String -Pattern `
        "settle timeout", `
        "reachability", `
        "retry", `
        "resume", `
        "submission order", `
        "lock release", `
        "durable state"
```

Inspect each match. Reject any new behavior for an excluded subject.

## 7. Commit, Rebase, and Run the Test-Quality Gate

Commit the exact manifest with a Conventional Commit subject:

```powershell
git add `
    src\interfaces\portals\upgrade_portal\upgrade\driver.py `
    src\interfaces\portals\upgrade_portal\upgrade\org_cascade\walk.py `
    src\interfaces\portals\upgrade_portal\app\assets\templates\partials\org_phase_list.html `
    tests\contract\upgrade_portal\test_org_phase_watch_contract.py `
    changelog.d\issue-3332-phase-watch-wording.md `
    specs\numbered\0\0\1\0\1\3\1\2\3332-phase-watch-submission-boundary
git commit -m "docs(upgrade): clarify the phase-watch submission boundary" `
    -m "Closes #3332" `
    -m "Co-authored-by: Copilot App <223556219+Copilot@users.noreply.github.com>"
git fetch --no-tags origin "+refs/heads/main:refs/remotes/origin/main"
git rebase origin/main
```

Rerun sections 2 through 6 after the rebase.

Run the committed test-quality gate:

```powershell
test-quality-analyzer --gate `
    --config .github/test-quality-config.toml `
    --baseline .github/test-quality-baseline.json `
    --changed-from "origin/main" `
    --full-gate-path .github/workflows/ci.yml `
    --full-gate-path requirements-dev.txt
```

Expected result: `gate: 0 new findings vs baseline`.

## 8. Push One Time

After all post-rebase checks pass, push one time:

```powershell
git push --force-with-lease origin `
    jmorrison-juniper-docs-3332-phase-watch-boundary
```

Do not push before the rebase. Do not push a second validation commit.

## 9. Verify Ready for Review

Use `.github/PULL_REQUEST_TEMPLATE.md` without changing its headings, comments,
checklist items, or order.

The pull request title is:

```text
docs(upgrade): clarify the phase-watch submission boundary
```

The body must include `Closes #3332`, the exact changed-file list, and each
command result from this guide.

Verify the pull request:

```powershell
gh pr view --json number,title,isDraft,baseRefName,headRefName,mergeable,reviewDecision,url
gh pr checks --watch
```

Ready-for-review conditions:

- The pull request targets `main`.
- The head branch is the issue branch.
- The title uses the approved Conventional Commit form.
- The pull request is not a draft.
- The body preserves the repository template.
- The diff contains only the approved implementation manifest and Spec Kit
  records.
- All required checks, including CodeQL, pass.
- The issue keeps `needs-human-review`.
- No auto-merge label is present.
- A human reviewer can confirm that the change is wording-only.
