# Quickstart: Issue 4389 reproduction and verification

## Part 1. Reproduce the refusal in the approved lab organization

Use the approved lab organization only. The owner asks that no resolve request repeat against production.

1. Start MistHelper with the approved lab organization.
2. Run a read-only list of Marvis Actions. Use mode 1 or mode 2 of menu 270.
3. Select one current open Marvis Action in the topic `gateway/vpn_path_down` (`model.py` line 74).
4. Run menu 270 again. Choose mode 3, the resolve flow.
5. Select the resolution code `suggested`. The first code is `suggested` (`model.py` line 126).
6. Type `RESOLVE 1` at the confirmation prompt.
7. Read the results file and the log. Do not acknowledge the alarm.

Caution: a successful resolve changes the Mist Action status. Mist can set the action back to Open.

Expected result before this change: one PUT request for each selected Marvis Action. The results file shows outcome `error` and HTTP status 403 for a refusal. The run continues to the next target.

Expected result after this change: one PUT request. The row shows outcome `error`, HTTP status 403, and a masked message. The run stops. Later rows show outcome `not_sent`.

## Part 2. Reproduce the defect offline

These commands use the fake session. They do not call Mist.

```powershell
python -m pytest tests/unit/marvis/actions/test_operation.py
```

Before the change, the run-level stop tests fail. The tests name the refusal statuses 401 and 403. Each failing test sends three PUT requests where the rule requires one.

```powershell
python -m pytest tests/unit/marvis/actions/test_client.py
```

Before the change, the masking tests fail. The tests check the UUID, the token value, and the email address. The 401 and 403 client tests pass before the change, because the 2xx rule already holds.

## Part 3. Verify the change

```powershell
python -m pytest tests/unit/marvis/actions/test_client.py
python -m pytest tests/unit/marvis/actions/test_operation.py
python -m pytest tests/guardrails/test_marvis_actions_portal_exposure.py
python -m pytest tests/guardrails/test_changelog_fragment_policy.py
python -m ruff check .
```

Expected results: each pytest command reports zero failures. The ruff command reports `All checks passed`.

## Part 4. Collect the cause evidence (human)

The cause stays unverified until a human completes these steps.

1. Open `data\OrgMarvisActionsResolveResults.csv`. Read the columns `outcome`, `http_status`, `message`, `verified_status`, `resolution_code`, and `resolve_time_iso`.
2. Open `data\script.log`. Find the WARNING line that names the HTTP status.
3. In the Mist UI, read the organization role of the account that owns the API token. The repository report names the roles admin, write, and helpdesk for the permission `canUpdateMarvisActionsStatus` (`documentation/marvis-actions-api-endpoints.md`, section Permissions).
4. In the Mist UI, open the same Marvis Action with the same account. Do not select a resolve control. Record whether the control appears.
5. If the role is outside admin, write, and helpdesk, stop. A human decides the credential policy (decision D-7 in `design/research.md`).
6. If the role is inside the list and the control appears, share the HTTP status and the masked message with the Mist support team.
7. If the role is inside the list and the control does not appear, record the result on issue 4389.

## Part 5. Cleanup

This record starts no container, creates no volume, and publishes no port. No cleanup command applies.
