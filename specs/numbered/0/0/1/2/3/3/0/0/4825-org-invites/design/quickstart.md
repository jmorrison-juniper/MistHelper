# Quickstart: Organization Invites Export Guard

Use these steps to reproduce the absent path and to run the checks for this issue. Run each command from the repository root. Activate the environment first. On Windows, run `.venv\Scripts\Activate.ps1`. On macOS or Linux, run `source .venv/bin/activate`.

## Step 1. Confirm that the installed mistapi has no list function

This command reads local attributes only. It makes no request to the Mist API.

Windows PowerShell:

```powershell
python -c "from mistapi.api.v1.orgs.invites import listOrgInvites"
python -c "from mistapi.api.v1.orgs.invites import inviteOrgAdmin, uninviteOrgAdmin, updateOrgAdminInvite"
```

Expected result: the first command fails with `ImportError: cannot import name 'listOrgInvites'`. The second command prints nothing, because the three functions exist.

macOS or Linux:

```bash
.venv/bin/python -c "from mistapi.api.v1.orgs.invites import listOrgInvites"
.venv/bin/python -c "from mistapi.api.v1.orgs.invites import inviteOrgAdmin, uninviteOrgAdmin, updateOrgAdminInvite"
```

## Step 2. Run the focused tests

```powershell
python -m pytest tests/unit/export/test_org_export_utils.py
```

Expected result: all tests pass, including `test_invites`, `test_invites_without_sdk_list_call_logs_error_and_skips`, and the log-order test added by T008.

## Step 3. Confirm the absent-path test can fail

Use the worktree for this step only. Do not commit the edit.

1. Replace the `getattr` call on line 726 of `src/operations/exporting/export/org_export_utils.py` with a direct read of `mistapi.api.v1.orgs.invites.listOrgInvites`.
2. Run `python -m pytest tests/unit/export/test_org_export_utils.py`.
3. Expected result: the absent-path test fails with `AttributeError`.
4. Restore the `getattr` call before any commit.

## Step 4. Run the guard tests

```powershell
python -m pytest tests/guardrails/test_markdown_links.py tests/guardrails/test_process_folder_structure.py
```

Expected result: all tests pass.

## Step 5. Confirm that the wrong link is gone

```powershell
Select-String -Path documentation\api\orgs\DELETE_orgs_org_id_invites_invite_id.md, documentation\api\orgs\POST_orgs_org_id_invites.md, documentation\api\orgs\PUT_orgs_org_id_invites_invite_id.md -Pattern 'GET_orgs_org_id_invites'
```

Expected result: no output.

## Step 6. Confirm the state of GitHub main

These commands read the remote state. Replace `<path>` with a repository path.

```bash
gh api "repos/jmorrison-juniper/MistHelper/contents/<path>?ref=main" --jq .sha
```

Expected result: the blob SHA of the file on main. Compare it with the blob SHA in `design/research.md`.

## Step 7. Run the remaining local gates

Run the commands in the Local gate table of `tasks.md`, task T-LOCAL-GATES. Record each result in the pull request body.
