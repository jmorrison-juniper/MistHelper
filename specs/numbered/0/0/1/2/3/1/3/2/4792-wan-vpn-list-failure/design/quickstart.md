# Quickstart: Verify the VPN Inventory Read

This guide reproduces the defect and verifies the fix. Run each command from the root of the worktree with its `.venv`. Each command is offline. Do not run `tests/integration/test_wan_vpn_builder_live.py`.

Caution: unset `MIST_APITOKEN` and `MIST_API_TOKEN` in the shell before you run these commands. Use the mocked test module only.

## Prerequisites

- A worktree on the branch `fix/4792-wan-vpn-list-failure`, created from `main`.
- A `.venv` created with `scripts/bootstrap_worktree.py`, as `.github/copilot-instructions.md` describes.
- The record folder copied from the draft to `specs/numbered/0/0/1/2/3/1/3/2/4792-wan-vpn-list-failure/` only after T006.

## Scenario 1: Reproduce the defect on unchanged code

Run the failure-class cases of the focused module.

```powershell
python -m pytest tests/unit/prod_readiness/standalone/operations/wan/test_wan_vpn_builder.py -q -k TestFetchExistingVpns
```

Expected on unchanged code:

- The case `test_api_error_returns_unavailable_inventory` fails. The unchanged code returns an empty list after the exception (`wan_vpn_builder.py` lines 393 to 406).
- Each HTTP refusal case, each malformed page case, and each pagination case fails.
- The case `test_verified_empty_inventory_returns_empty_list` passes. A verified empty read keeps its result.

## Scenario 2: Verify the change

Compile the two Python files.

```powershell
python -m py_compile src/operations/wan/vpn_inventory.py src/operations/wan/wan_vpn_builder.py
```

Expected: no output.

Run the focused module.

```powershell
python -m pytest tests/unit/prod_readiness/standalone/operations/wan/test_wan_vpn_builder.py -q
```

Expected: all 25 cases pass.

Count the methods of the builder class. Record the count before you edit the file. The count after the change must equal the count before the change (SC-006).

```powershell
(Select-String -Path src\operations\wan\wan_vpn_builder.py -Pattern '^    def ').Count
```

## Scenario 3: Regenerate the menu pages

Run both generators. Then run the check.

```powershell
python scripts/generate_menu_wiki.py
python -m scripts.menu_api_map
python -m scripts.menu_api_map --check
```

Expected: the check exits with code 0. Run the two generators a second time. The second run changes no file.

Run `git status --short`. The output lists only these paths: `src/operations/wan/vpn_inventory.py`, `src/operations/wan/wan_vpn_builder.py`, the focused test module, `changelog.d/issue-4792-wan-vpn-list-failure.md`, the record folder, and the generated pages that the generator changed.

## Scenario 4: Repository guards for the release note and the record

```powershell
python -m pytest tests/guardrails/test_process_folder_structure.py tests/guardrails/test_changelog_fragment_policy.py -q
ste-linter --config .ste-linter.toml --min-score 80 changelog.d/issue-4792-wan-vpn-list-failure.md
```

Expected: the tests pass. The linter scores the file at 80 or above.

## Scenario 5: Owner header check before merge

The owner runs one read-only `listOrgVpns` request for one organization. The request runs outside this repository, with a read token that the owner controls. The owner records only these facts:

- Whether `X-Page-Total` is present.
- Whether `X-Page-Limit` is present.
- Whether `X-Page-Page` is present.

The owner does not record the token, and the owner does not record record data. If any header is absent on a complete page, the owner stops the merge and follows the rollback in `plan.md`.

## Expected Results Summary

| Scenario | Command | Expected |
|----------|---------|----------|
| 1 | Focused module on unchanged code | Failure-class cases fail. The verified empty case passes. |
| 2 | Focused module after the change | All 25 cases pass. |
| 2 | Method count of `WanVpnBuilder` | The count equals the count before the change. |
| 3 | `python -m scripts.menu_api_map --check` | Exit code 0. |
| 4 | Guard tests and STE linter | Tests pass. The score is 80 or above. |
| 5 | Owner header check | Header facts recorded in the pull request. |
