# Quickstart: Laptop Branch Archive Verification

Use these commands to reproduce each check of issue 4868. Every GitHub command is a GET request. Every local git command reads refs only. Run each command from the repository root, `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper`.

Warning: do not run a checkout, fetch, pull, rebase, reset, or push for these checks. Each of those commands changes a branch or a ref.

## Prerequisites

1. Run `gh auth status`. The active account must read `jmorrison-juniper/MistHelper`.
2. Use PowerShell 7 or Windows PowerShell with the `gh` CLI on the `PATH`.
3. Run no repository script for these checks.

## Scenario 1: Read the issue body and count the listed names

```powershell
gh issue view 4868 -R jmorrison-juniper/MistHelper --json body --jq .body
```

Expected result: the reference block holds 497 lines that start with a count and a tab. The counts sum to 2,087.

## Scenario 2: List the archive refs on origin (TC-01)

```powershell
gh api --paginate "repos/jmorrison-juniper/MistHelper/git/matching-refs/heads/archive/laptop-20261121/" --jq '.[] | .ref + " " + .object.sha' | Measure-Object
```

Expected result: 491 lines. The output includes `refs/heads/archive/laptop-20261121/stash-0`.

## Scenario 3: List the rescue branches and their parent counts (TC-02)

```powershell
gh api --paginate "repos/jmorrison-juniper/MistHelper/git/matching-refs/heads/rescue/uncommitted-20261121-" --jq '.[] | .object.sha' | ForEach-Object { gh api "repos/jmorrison-juniper/MistHelper/commits/$_" --jq '.parents | length' }
```

Expected result: six lines, and each line reads `1`.

## Scenario 4: Compare the archive tips with the data model (TC-03)

```powershell
gh api --paginate "repos/jmorrison-juniper/MistHelper/git/matching-refs/heads/archive/laptop-20261121/" --jq '.[] | .ref + " " + .object.sha' | ForEach-Object { ($_ -split ' ')[0].Replace('refs/heads/archive/laptop-20261121/', '') + ' ' + ($_ -split ' ')[1].Substring(0, 7) }
```

Expected result: 491 lines of the form `<archived name> <tip of seven characters>`. Compare each line with the matching row of the table in `design/data-model.md`. Expected result: no line differs.

## Scenario 5: Classify the counterpart states (TC-04)

```powershell
gh api --paginate "repos/jmorrison-juniper/MistHelper/git/matching-refs/heads/" --jq '.[] | .ref' | Where-Object { $_ -notlike 'refs/heads/archive/*' } | Measure-Object
```

Expected result: the count of non-archive branches is 107. Compare the names in the table with the output. The name `jmorrison-juniper-4200-migrate-mistwanperformance` appears once, and its tip is `843be63`. The six rescue names appear once each. No other archived name appears.

Check the one same-name branch directly:

```powershell
gh api "repos/jmorrison-juniper/MistHelper/git/ref/heads/jmorrison-juniper-4200-migrate-mistwanperformance" --jq .object.sha
```

Expected result: `843be63bc837513b4442dae69da9f0db922e0ed1`.

## Scenario 6: Compare the diverged tips (RC-37)

```powershell
$threeDots = '.' * 3
gh api ("repos/jmorrison-juniper/MistHelper/compare/843be63bc837513b4442dae69da9f0db922e0ed1" + $threeDots + "d77a900f9ec4db7149f90f324f1ade7772a6243d") --jq '{status: .status, ahead_by: .ahead_by, behind_by: .behind_by}'
```

Expected result: `status` reads `diverged`, `ahead_by` reads 48, and `behind_by` reads 85. The compare base is the same-name branch. The head is the archive tip. So the archive tip holds 48 commits that the same-name branch lacks, and the same-name branch holds 85 commits that the archive tip lacks.

## Scenario 7: Check the stash ref and its source branch (RC-30, RC-38)

```powershell
gh api "repos/jmorrison-juniper/MistHelper/git/ref/heads/archive/laptop-20261121/stash-0" --jq .object.sha
gh api "repos/jmorrison-juniper/MistHelper/git/ref/heads/jmorrison-juniper-documented-trend-object-export" --jq .object.sha
```

Expected result: the first command prints `9d96feb696df742bcda242ee4b439060168b873d`. The second command returns `Not Found (HTTP 404)`, which shows that the source branch is absent.

## Scenario 8: Cross-check the local refs (TC-06)

```powershell
git -C "C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper" for-each-ref '--format=%(refname)' refs/heads/ | Measure-Object
git -C "C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper" for-each-ref '--format=%(refname)' refs/remotes/origin/archive/laptop-20261121/ | Measure-Object
```

Expected result: 330 local heads and 491 remote-tracking archive refs. Run the two commands again after the verification. The counts must match the first run.

## Scenario 9: Check the route and the child counts on main (TC-08)

```powershell
gh api "repos/jmorrison-juniper/MistHelper/git/trees/main?recursive=1" --jq '[.tree[] | select(.path | test("^specs/numbered/0/0/1/2/3/4/3/[^/]+$")) | .path] | length'
gh api "repos/jmorrison-juniper/MistHelper/git/trees/main?recursive=1" --jq '[.tree[] | select(.path | test("^specs/numbered/0/0/1/2/3/[^/]+$")) | .path] | length'
```

Expected result: the first command prints 2. The second command prints 5. The route folder `specs/numbered/0/0/1/2/3/4/3/3` is absent from the tree.

## Scenario 10: Check the changelog directory count (RC-28)

```powershell
gh api "repos/jmorrison-juniper/MistHelper/git/trees/main?recursive=1" --jq '[.tree[] | select(.path | test("^changelog[.]d/[^/]+$")) | .path] | length'
```

Expected result: 335.

## Test Cases

Each test case names its requirements. Run each test case after the record reaches the repository.

- **TC-01** (FR-001, SC-001): Scenario 2 prints 491 lines.
- **TC-02** (FR-002, SC-002): Scenario 3 prints six lines of `1`.
- **TC-03** (FR-003): Scenario 4 reports zero mismatches against the table.
- **TC-04** (FR-004, SC-003): Scenario 5 shows one same-name branch and six rescue names with their own branch.
- **TC-05** (FR-005, FR-006): The count of listed names is 497. The count of archive refs is 491 (TC-01). The count of rescue branches is 6 (TC-02). The sum of 491 and 6 is 497.
- **TC-06** (FR-007, FR-008, SC-005): Scenario 8 prints the same counts before and after the verification.
- **TC-07** (FR-009): Search the quickstart for write flags in its GitHub commands. The command below prints nothing.

  ```powershell
  Select-String -Path "specs\numbered\0\0\1\2\3\4\3\3\4868-laptop-branch-archive\design\quickstart.md" -Pattern '^gh api.*(\s-X\s|--method|\s-f\s|\s-F\s|--field)'
  ```

- **TC-08** (FR-012): Scenario 9 prints 2 and 5.
- **TC-09** (FR-012): The record folder holds five children, and the `design` folder holds five children.

  ```powershell
  (Get-ChildItem -LiteralPath "specs\numbered\0\0\1\2\3\4\3\3\4868-laptop-branch-archive" -Force).Count
  (Get-ChildItem -LiteralPath "specs\numbered\0\0\1\2\3\4\3\3\4868-laptop-branch-archive\design" -Force).Count
  ```

- **TC-10** (SC-004): The count of rows that start with `RC-` in `design/research.md` equals the count of `remote_checks` in the status file. Both counts equal 39.

  ```powershell
  (Select-String -Path "specs\numbered\0\0\1\2\3\4\3\3\4868-laptop-branch-archive\design\research.md" -Pattern '^\| RC-\d{2} \|').Count
  ```

- **TC-11** (FR-011): The human decision marker appears once in `design/research.md`, in decision D-8. The pattern brackets keep the command from matching its own text.

  ```powershell
  Select-String -Path "specs\numbered\0\0\1\2\3\4\3\3\4868-laptop-branch-archive\design\research.md" -Pattern 'HUMAN-DECISION-[R]EQUIRED'
  ```

- **TC-12** (FR-015): The record holds no placeholder text. The command below prints nothing. The pattern brackets keep the command from matching its own text.

  ```powershell
  Get-ChildItem -LiteralPath "specs\numbered\0\0\1\2\3\4\3\3\4868-laptop-branch-archive" -Recurse -File | Select-String -Pattern 'T[B]D|TOD[O]|to be [d]ecided|\.\.\.'
  ```

- **TC-13** (FR-013, SC-006): The STE gate scores each Markdown file at 80 or above. The command is in `tasks.md`, task T-LOCAL-GATES.
- **TC-14** (FR-014): The guardrail suite passes, including the changelog fragment policy.

  ```powershell
  python -m pytest tests/guardrails
  ```

- **TC-15** (FR-010): The Unverified list in `design/research.md` holds exactly eight numbered items. Each item gives a reason.

  ```powershell
  (Select-String -Path "specs\numbered\0\0\1\2\3\4\3\3\4868-laptop-branch-archive\design\research.md" -Pattern '^[0-9]+\. ').Count
  ```

  Expected result: 8.
