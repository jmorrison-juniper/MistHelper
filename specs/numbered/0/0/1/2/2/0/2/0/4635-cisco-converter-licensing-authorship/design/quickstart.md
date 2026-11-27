# Quickstart: Reproduce the evidence for issue 4635

Use these steps to repeat the evidence checks. The steps use read calls only, except the verification commands in section 7. Do not print the value of any token variable.

## 1. Prepare GitHub read access

Set the host. Set the token from the variable with the account name. The variable holds the token, so do not print it.

```powershell
$env:GH_HOST = 'github.com'
$env:GH_TOKEN = $env:COPILOT_GH_ACCOUNT_github_2E_com_jmorrison_2D_juniper
```

## 2. Read the issue and the pull requests

```powershell
gh issue view 4635 -R jmorrison-juniper/MistHelper --json number,title,body,state,labels,comments,createdAt,updatedAt,author
gh pr list -R jmorrison-juniper/MistHelper --state all --search "4635" --json number,title,state,headRefName,url,mergedAt
```

Expected: the issue reports OPEN. The pull request search returns an empty list.

## 3. Check the route leaf on main

```powershell
gh api "repos/jmorrison-juniper/MistHelper/git/trees/main?recursive=1" --jq ".tree[] | .path" | Select-String -Pattern "0/0/1/2/2/0/2/0"
```

Expected: no output. The leaf is absent (RC-25).

## 4. Read a remote file and print line numbers

This example reads the MistHelper license and prints each line that names NonCommercial.

```powershell
$out = gh api "repos/jmorrison-juniper/MistHelper/contents/LICENSE?ref=main" --jq ".sha, .content"
$base64 = ($out[1..($out.Count - 1)]) -join ""
$lines = [Text.Encoding]::UTF8.GetString([Convert]::FromBase64String($base64)) -split '\r?\n'
foreach ($index in 0..($lines.Count - 1)) { if ($lines[$index] -match "NonCommercial") { "$($index + 1): $($lines[$index])" } }
```

Expected: three lines print, numbered 1, 5, and 13. Line 13 states the NonCommercial term of the MistHelper license (RC-01 to RC-03 cite the other lines).

## 5. Verify the source license at the pinned commit

```powershell
gh api "repos/jmorrison-juniper/MistCiscoConfigConverter/contents/LICENSE?ref=d9be92f91e0f74fef711e9f7d30b59bf71ffdf4c" --jq ".sha"
```

Expected: e9ae5eff92457c2372db3be30a3d99166aeee547 (RC-50).

## 6. Verify the source default branch head

```powershell
gh api "repos/jmorrison-juniper/MistCiscoConfigConverter/commits/main" --jq ".sha"
```

Expected: d9be92f91e0f74fef711e9f7d30b59bf71ffdf4c (RC-49).

## 7. Verification commands for the implementation phase

Run these commands in T-LOCAL-GATES and T-PR. Run them from the repository root in the repository virtual environment.

```powershell
python -m py_compile MistHelper.py
python -m pytest tests/guardrails/test_process_folder_structure.py
ste-linter --config .ste-linter.toml --min-score 80 specs/numbered/0/0/1/2/2/0/2/0/4635-cisco-converter-licensing-authorship/spec.md specs/numbered/0/0/1/2/2/0/2/0/4635-cisco-converter-licensing-authorship/plan.md specs/numbered/0/0/1/2/2/0/2/0/4635-cisco-converter-licensing-authorship/tasks.md specs/numbered/0/0/1/2/2/0/2/0/4635-cisco-converter-licensing-authorship/analysis.md specs/numbered/0/0/1/2/2/0/2/0/4635-cisco-converter-licensing-authorship/design/research.md specs/numbered/0/0/1/2/2/0/2/0/4635-cisco-converter-licensing-authorship/design/data-model.md specs/numbered/0/0/1/2/2/0/2/0/4635-cisco-converter-licensing-authorship/design/quickstart.md specs/numbered/0/0/1/2/2/0/2/0/4635-cisco-converter-licensing-authorship/design/checklists/requirements.md specs/numbered/0/0/1/2/2/0/2/0/4635-cisco-converter-licensing-authorship/design/checklists/decisions.md specs/numbered/0/0/1/2/2/0/2/0/4635-cisco-converter-licensing-authorship/design/checklists/provenance.md
```

Expected: the compile command prints no output. The guard test passes and prints its examined counts. Each STE result scores 80 or above.

## 8. Count checks for the consistency review

Run these counts in the record folder. Both counts must equal 77.

```powershell
(Select-String -Path "design/research.md" -Pattern "^\| RC-").Count
(Get-Content -Raw "../_meta/4635-STATUS.json" | ConvertFrom-Json).remote_checks.Count
```

## 9. Read the legal text

Open these two pages and read the sections named in research.md:

- https://creativecommons.org/licenses/by-nc/4.0/legalcode (Section 1, item 9)
- https://creativecommons.org/licenses/by-nc-sa/4.0/legalcode (Section 1, item 3, and Section 3(b))
