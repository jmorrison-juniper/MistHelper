# Quickstart: Repository Sync Branch Preservation

Use this file for the read-only checks and the writer steps. The author role runs sections 1 to 5. The owner or an approved writer runs sections 6 to 8.

## 1. Set the variables

Run these lines in each new PowerShell session. They set the clone path and the GitHub host. They do not print the token.

```powershell
$repo = 'C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper'
$recordDir = 'C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\specs\numbered\0\0\1\1\1\3\3\4\3969-repository-sync-branch-preservation'
$env:GH_HOST = 'github.com'
$env:GH_TOKEN = $env:COPILOT_GH_ACCOUNT_github_2E_com_jmorrison_2D_juniper
```

Warning: printing the value of GH_TOKEN exposes the credential. Never print it.

Set both variables in the shell before each gh command.

## 2. Read the issue (VC-02)

```powershell
gh issue view 3969 -R jmorrison-juniper/MistHelper --json number,title,state,comments
```

## 3. Remote checks (VC-01)

File rows read the remote tree. Each line prints a path and its blob SHA.

```powershell
$tree = (gh api "repos/jmorrison-juniper/MistHelper/git/trees/main?recursive=1" | Out-String) | ConvertFrom-Json
$tree.tree | Where-Object { $_.path -eq 'AGENTS.md' } | ForEach-Object { $_.path + ' ' + $_.sha }
```

Line rows read one line of the remote file body. Set the path and the line number first.

```powershell
$filePath = 'AGENTS.md'
$lineNumber = 169
$json = (gh api ('repos/jmorrison-juniper/MistHelper/contents/' + $filePath + '?ref=main') | Out-String) | ConvertFrom-Json
$text = [Text.Encoding]::UTF8.GetString([Convert]::FromBase64String(($json.content -replace '\s', '')))
($text -split "`n")[$lineNumber - 1]
```

Branch rows check one GitHub branch. A present branch returns a commit SHA. An absent branch returns HTTP 404.

```powershell
$name = 'backup/3671-pre-subject-rewrite-20261003'
gh api ('repos/jmorrison-juniper/MistHelper/branches/' + $name) --jq '.commit.sha'
```

Pull request rows read one pull request.

```powershell
$prNumber = 3967
gh pr view $prNumber -R jmorrison-juniper/MistHelper --json number,state,isDraft,mergeStateStatus,mergedAt,headRefName,headRefOid
```

## 4. Local classification (VC-06)

This loop assigns each local branch to one class. It changes no ref.

```powershell
$mergedRaw = gh pr list -R jmorrison-juniper/MistHelper --state merged --limit 5000 --json number,headRefName,headRefOid | Out-String | ConvertFrom-Json
$openRaw = gh pr list -R jmorrison-juniper/MistHelper --state open --limit 500 --json number,headRefName | Out-String | ConvertFrom-Json
$remoteNames = @(gh api --paginate "repos/jmorrison-juniper/MistHelper/branches?per_page=100" --jq '.[].name' | Where-Object { $_ })
$headMap = @{}
foreach ($pr in ($mergedRaw | Sort-Object number)) {
    $headMap[$pr.headRefName] = [pscustomobject]@{
        Number = $pr.number
        Oid = $pr.headRefOid
    }
}
$classLines = foreach ($ref in @(git -C $repo for-each-ref '--format=%(refname:short)' refs/heads | Where-Object { $_ -and $_ -ne 'main' })) {
    $tip = (git -C $repo rev-parse ('refs/heads/' + $ref) | Out-String).Trim()
    $ahead = [int]((git -C $repo rev-list --count ('origin/main..refs/heads/' + $ref) | Out-String).Trim())
    $openHit = @($openRaw | Where-Object { $_.headRefName -eq $ref }).Count
    if ($ahead -eq 0) { $class = 'A' }
    elseif ($openHit -gt 0) { $class = 'G' }
    elseif ($headMap.ContainsKey($ref) -and $tip -eq $headMap[$ref].Oid) { $class = 'B' }
    elseif ($headMap.ContainsKey($ref)) { $class = 'C' }
    elseif ($remoteNames -contains $ref) { $class = 'F' }
    elseif (@(git -C $repo cherry origin/main ('refs/heads/' + $ref) | Where-Object { $_.StartsWith('+') }).Count -gt 0) { $class = 'D' }
    else { $class = 'E' }
    $class + ' ' + $ref
}
$classLines | Group-Object { $_.Split(' ')[0] } | Select-Object Name, Count
```

Expected counts: class A 4, class B 135, class C 129, class D 47, class E 7, class F 7, and class G 0.

## 5. Merge and cherry checks for class E (VC-07)

Run these lines for each class E branch. Set the name first.

```powershell
$name = 'tmp/2729-rebase'
git -C $repo rev-list --merges --count ('origin/main..refs/heads/' + $name)
git -C $repo cherry origin/main ('refs/heads/' + $name)
```

Expected result: the merge count is 0. The cherry output has one line, and that line starts with a minus sign.

## 6. Writer steps (owner or approved writer)

Step S1 posts the claim (task T001). Write the claim text to a file in the user profile first.

```powershell
gh issue comment 3969 -R jmorrison-juniper/MistHelper --body-file (Join-Path $env:USERPROFILE 'misthelper-3969-claim.md')
```

Step S2 records the worktree inventory (task T003). The owner decides each discard (decision D-5).

```powershell
git -C $repo worktree list --porcelain
git -C $worktreePath status --porcelain
```

Set `$worktreePath` to each path from the first command, then run the second command for that path.

Step S3 saves the ref snapshot before any deletion. The file stays outside the repository.

```powershell
git -C $repo for-each-ref '--format=%(refname) %(objectname)' refs/heads | Out-File -FilePath (Join-Path $env:USERPROFILE 'misthelper-3969-ref-snapshot.txt') -Encoding ascii
```

Step S4 creates the class C and class D tags (tasks T004 and T005). The tag names use the UTC date of the run.

```powershell
$date = (Get-Date).ToUniversalTime().ToString('yyyyMMdd')
$classCD = @($classLines | Where-Object { $_ -match '^[CD] ' } | ForEach-Object { $_.Substring(2) })
foreach ($name in $classCD) {
    $tagName = 'archive/preservation/3969-' + ($name -replace '/', '-') + '-' + $date
    $tip = (git -C $repo rev-parse ('refs/heads/' + $name) | Out-String).Trim()
    git -C $repo tag $tagName $tip
}
```

The `git tag` command stops for an existing name. The writer does not add a force option.

Step S5 checks that each tag resolves to its branch tip (VC-03). The loop prints a line only for a mismatch.

```powershell
foreach ($name in $classCD) {
    $tagName = 'archive/preservation/3969-' + ($name -replace '/', '-') + '-' + $date
    $resolved = (git -C $repo rev-parse --verify --quiet ('refs/tags/' + $tagName + '^{commit}') | Out-String).Trim()
    $tip = (git -C $repo rev-parse ('refs/heads/' + $name) | Out-String).Trim()
    if ($resolved -ne $tip) { Write-Output ('Mismatch for ' + $tagName) }
}
```

Step S6 creates the five pull request head tags (task T006). Each commit must exist locally first.

```powershell
foreach ($prNumber in @(3954, 3955, 3956, 3957, 3973)) {
    $headOid = (gh pr view $prNumber -R jmorrison-juniper/MistHelper --json headRefOid --jq '.headRefOid' | Out-String).Trim()
    git -C $repo cat-file -t $headOid
    git -C $repo tag ('archive/preservation/3969-pr' + $prNumber + '-head-' + $date) $headOid
}
```

Step S7 pushes each new tag by its name (task T007).

```powershell
$newTags = @(git -C $repo tag --list 'archive/preservation/3969-*')
foreach ($tagName in $newTags) {
    git -C $repo push origin $tagName
}
```

Warning: the --tags option selects every local tag for the push. Do not use that option.

Step S8 counts the remote tags (VC-04). The expected result is 181.

```powershell
gh api 'repos/jmorrison-juniper/MistHelper/git/matching-refs/tags/archive/preservation/3969-' --jq 'length'
```

Step S9 posts the proof comment (task T008). Write the proof text to a file in the user profile first.

```powershell
gh issue comment 3969 -R jmorrison-juniper/MistHelper --body-file (Join-Path $env:USERPROFILE 'misthelper-3969-proof.md')
```

Step S10 deletes local branches at passed gates (tasks T009 to T012). Use the lowercase option for class A only.

```powershell
git -C $repo branch -d $name
```

Use the uppercase option for classes B, C, D, and E after each gate passes.

```powershell
git -C $repo branch -D $name
```

Warning: the uppercase option forces the deletion of a branch. Run it only after the gate for that class passes.

Step S11 refreshes the container after claim release (task T016). Set the location to the clone first.

```powershell
Set-Location $repo
podman build -t misthelper:local .
podman rm -f misthelper-app
.\scripts\compose.ps1 up -d --no-deps misthelper
podman ps
podman volume ls --filter "name=misthelper-"
```

Warning: never run a volume removal or a prune command during this refresh.

Caution: stop any running capture before the refresh starts.

## 7. Verification commands

| ID | Requirement | Command | Expected result |
| - | - | - | - |
| VC-01 | FR-001 | The commands in section 3 | Each row in design/research.md repeats its result, or the row records a change |
| VC-02 | FR-002 | The command in section 2 | One claim comment exists before the first write |
| VC-03 | FR-003, FR-004 | The loop in step S5 | No mismatch line appears |
| VC-04 | FR-003, FR-004 | The command in step S8 | The result is 181 |
| VC-05 | FR-005 | The commands in step S6 | Each head commit prints commit |
| VC-06 | FR-006 | The loop in section 4 | Class A branches show zero commits beyond origin/main. Class B tips equal their merged head |
| VC-07 | FR-007 | The commands in section 5 | The merge count is 0 and the cherry output has one minus line |
| VC-08 | FR-008 | The branch command in section 3 for each class F name | Each local tip equals its GitHub tip |
| VC-09 | FR-009 | `git --no-optional-locks -C $repo status --porcelain` | The five modified paths appear unchanged |
| VC-10 | FR-010 | The commands in step S2 | An inventory comment exists on issue 3969 before any deletion |
| VC-11 | FR-011 | The command in section 2 | One proof comment exists after step S9 |
| VC-12 | FR-012 | `gh pr view` with `--json state --jq '.state'` for each named pull request | Each result is MERGED or CLOSED |
| VC-13 | FR-013 | `podman volume ls --filter "name=misthelper-"` | Both misthelper-arangodb-data and misthelper-redis-data appear |
| VC-14 | FR-014 | `(Get-ChildItem -LiteralPath $recordDir).Count` for each directory of the record | Each count is five or fewer |
| VC-15 | FR-015 | `ste-linter --config .ste-linter.toml --min-score 80` with the record Markdown files | Each file scores 80 or above |
| VC-16 | FR-016 | `Select-String -LiteralPath (Join-Path $recordDir 'design\research.md') -Pattern '^- U-'` | Twelve unverified items appear, each with a reason |

## 8. Rollback

Remove a preservation tag only after the owner approves the removal.

```powershell
git -C $repo push origin --delete $tagName
git -C $repo tag -d $tagName
```

Warning: removing a preservation tag can leave its commits without a remote copy. Confirm another copy exists first.

Restore a class C or class D branch from its tag.

```powershell
git -C $repo branch $name $tagName
```

Restore a class A, B, or E branch from the snapshot file saved in step S3. Use the object name listed for that branch.

```powershell
git -C $repo branch $name $sha
```

Start the previous container image by its tag. The previous image tag is unverified (U-3).
