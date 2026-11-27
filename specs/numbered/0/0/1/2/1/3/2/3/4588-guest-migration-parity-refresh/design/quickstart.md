# Quickstart: reproduce the evidence and run the planning gates

This file lists exact commands for the next step. The planning run did not execute these commands, because the brief forbids repository scripts and builds. Run each command from the MistHelper repository root, unless the command names another path.

## 1. Re-pin source and target

```powershell
gh api repos/jmorrison-juniper/MistGuestAuthorizations/commits/main --jq .sha
gh api repos/jmorrison-juniper/MistHelper/commits/main --jq .sha
```

Expected results at this evidence date: the source prints `0213240cb9edfa237f763acd156b90a6049363cb`, and the target prints `f03c6c9b36d612a48d7b9652998c2fd87dd777ca`. If either value changes, repeat the evidence in [research](research.md) before implementation. Record the new values in [research section 2](research.md#2-pins-and-freshness).

Set the GitHub host and token before each `gh` command, as the brief directs. Do not print the token value.

## 2. Compare local blobs with GitHub main

```powershell
$tree = ConvertFrom-Json ((gh api "repos/jmorrison-juniper/MistHelper/git/trees/main?recursive=1") -join [Environment]::NewLine)
$tree.tree | Where-Object { $_.path -eq 'compose.yml' } | ForEach-Object { $_.path + ' ' + $_.sha }
git hash-object -- compose.yml
```

The two blob values must match for each cited target file. A mismatch means the local file is not the GitHub file. Use the GitHub blob for evidence in that case.

## 3. Verify each source blob

```powershell
$sourceTree = ConvertFrom-Json ((gh api "repos/jmorrison-juniper/MistGuestAuthorizations/git/trees/0213240cb9edfa237f763acd156b90a6049363cb?recursive=1") -join [Environment]::NewLine)
$sourceTree.tree | Where-Object { $_.type -eq 'blob' } | Measure-Object | ForEach-Object { $_.Count }
```

The command must print 39. Seven of the blob paths end with `.png`.

## 4. Verify the spec route

The route for issue 4588 is `0/0/1/2/1/3/2/3`. The route follows the base-5 digits of 4588, padded to eight places (T19 L4). The repository script was not run. Confirm the route by reading `.specify/scripts/powershell/spec-route.ps1` in a separate review.

## 5. Planning gates for this record

Run each gate on the record files and on the changelog fragment.

```text
.venv\Scripts\ste-linter.exe --config .ste-linter.toml --min-score 80 <each Markdown file in the record>
check-citations <record folder>
markdown-link-check --root . <record folder>
speckit-task-audit --root .
git diff --check
```

- The STE command follows the STE row in documentation/quality-gates.md at line 283. Each file must score 80 or above.
- The citation command follows the `citation_lint` row in documentation/quality-gates.md at line 66.
- The link and task-audit commands come from the tool list in the repository instructions and documentation/quality-gates.md at line 18.
- The task audit is advisory. Record its exact output. Do not change its allow-list.

Record the exact result of each command in the pull request. A command that does not run counts as not run.

## 6. Projection tests (future, no change in this planning PR)

```text
python -m pytest tests/unit/web_portal/test_guest_authorization_read_model.py
```

The file holds 22 test cases (T02). This planning PR changes no Python file, so the command is not a gate for this PR.

## 7. Changelog fragment

Name the fragment `changelog.d/issue-4588-guest-migration-parity-refresh.md` when the pull request does not exist. Rename it to `pr-<number>.md` after the pull request exists. Write one heading and one bullet for each change type. Do not edit `CHANGELOG.md` on the work branch. The repository instructions name this rule in the section "Git and GitHub in this repository" at line 431.

## 8. Count checks

- Count the `remote_checks` rows in the STATUS file. The count must be 71.
- Count the rows in the remote verification table in [research section 8](research.md#8-remote-verification-table). The count must be 71.
- Count the requirement lines in [spec](../spec.md). The count must be 35.
- Count the task lines in [tasks](../tasks.md). The count must be 44.
- Count the test families in [E2E](contracts/e2e.md). The count must be 35.
