# MSP (Managed Service Provider) Support

MistHelper supports MSP-level operations for users with Managed Service Provider privileges. This enables bulk operations across multiple organizations from a single session.

## Enabling MSP Mode

MSP mode needs a credential that carries an MSP grant. Two kinds of credential do.

1. **Interactive login (`--login`, or menu 143 in a running session)**: The terminal asks for the Mist cloud, the email, and the password. If the account requires two-factor authentication, it also asks for the code. A wrong or empty code ends the login.

   ```text
   python MistHelper.py --login
   ```

   In a running session, choose the same login from the menu:

   ```text
   Select menu option: 143
   ```

   This switches from the token to the login and detects the MSP privileges.

2. **A user API token**: A token that you create under your own account carries the privileges of that account, including an MSP grant. It never asks for a 2FA code, so it suits a scheduled job and a container. An organization token carries no MSP grant.

3. **Automatic Detection**: After a login, MistHelper detects and displays your MSP access:

   ```text
   + MSP access detected: 2 MSP(s) available
     - Example MSP (role: admin)
   ```

   With a token, menu 309 prints the scope at step 1 of its run.

[Sign in for an MSP run](../operator-guide.md#sign-in-for-an-msp-run) gives the start command of each front end, the prompts, and the grants that give MSP scope.

## MSP-Enabled Operations

| Menu | Operation | Category | MSP Capability |
|------|-----------|----------|----------------|
| **154** | Advanced AP firmware upgrade | `destructive` | Mode 3: Upgrade across multiple orgs |
| **157** | Org-Level AP firmware upgrade | `destructive` | Mode 2: Multi-org upgrade with the org-level API |
| **168** | Site auto-upgrade configuration | `destructive` | Mode 2: Configure ALL sites across multiple orgs |

Warning: All three operations are destructive. Each one changes the Mist cloud
configuration and needs a typed confirmation. Use `--dry-run` first.

## Read-Only MSP Reports

| Menu | Operation | Documentation |
|------|-----------|---------------|
| **308** | Cross-org subscription, deployed inventory, and stock | [Cross-org report](../cross-org-subscription-stock.md) |
| **309** | EX switch hardware inventory of every organization in scope, as one CSV report and one XML file | [Operator guide](../operator-guide.md#sign-in-for-an-msp-run) |

Both operations read only. Menu 309 opens one read-only shell on each connected EX switch. It covers every organization that the account can reach, and it needs no MSP selection.

## Using MSP Multi-Org Mode

When MSP privileges are detected, supported menus offer an additional mode:

```text
  MSP privileges detected. Select operation mode:

    [1] Single Organization - upgrade APs in current org
    [2] MSP Multi-Org - select orgs from your MSP(s)

  Select mode (1-2) [1]: 2
```

## MSP Selection Interface

Flexible selection patterns for MSPs and organizations:

| Pattern | Example | Result |
|---------|---------|--------|
| Single index | `1` | First item |
| Multiple indices | `1,3,5` | Items 1, 3, and 5 |
| Range (dash) | `1-5` | Items 1 through 5 |
| Range (word) | `1 through 5` | Items 1 through 5 |
| All items | `all` | Every item |
| Cancel | `q` | Exit selection |

## Workflow Example: Multi-Org Firmware Upgrade

1. Run menu 143 to switch to interactive login
2. Run menu 157 (Org-Level AP Firmware Upgrade)
3. Select mode 2 (MSP Multi-Org)
4. Select MSP(s): "all" or "1,2"
5. For each MSP, select organizations: "1-10" or "all"
6. Configure upgrade settings (strategy, scheduling)
7. Confirm and execute -- upgrades run sequentially per org

## Workflow Example: Multi-Org Auto-Upgrade Configuration

1. Run menu 143 to switch to interactive login
2. Run menu 168 (Site Auto-Upgrade Configuration)
3. Select mode 2 (MSP Multi-Org)
4. Select MSP(s): "all" or "1,2"
5. For each MSP, select organizations: "1-10" or "all"
6. Configure shared schedule (day of week, time of day)
7. Each org is processed: all sites auto-selected, latest stable firmware chosen
8. Summary shows total sites configured across all orgs

## MSP Session Persistence

Once you select an MSP in menu 143, MistHelper remembers it for subsequent operations:

- Menu 157 offers your current MSP as the default
- Press Enter to use the previously selected MSP
- Or select different MSP(s) as needed

## Technical Notes

- **API Differences**: MSP operations use `mistapi.api.v1.msps.orgs.listMspOrgs()` to enumerate organizations
- **Dry-Run Support**: All MSP upgrade modes support `--dry-run` for safe validation
- **Global Variable**: MSP state stored in `msp_privileges` list and `selected_msp` dict
- **Detection Function**: `detect_msp_privileges()` runs after an interactive login and after a token session starts
- **Menu 309**: Reads the grants of the profile itself and covers every MSP of the account. It does not use `selected_msp`
- **Orggroup Grants**: A grant with the `orggroup`, `site`, or `sitegroup` scope adds no organization to the run of menu 309
