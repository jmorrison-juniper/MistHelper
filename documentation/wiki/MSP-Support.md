# MSP (Managed Service Provider) Support

MistHelper supports MSP-level operations for users with Managed Service Provider privileges. This enables bulk operations across multiple organizations from a single session.

## Enabling MSP Mode

1. **Use Interactive Login (Menu 115)**: MSP privileges require email/password authentication, not API tokens

   ```text
   Select menu option: 115
   ```

   This switches from token-based auth to interactive login and automatically detects MSP privileges.

2. **Automatic Detection**: On successful login, MistHelper detects and displays your MSP access:

   ```text
   + MSP access available: 2 MSP(s)
   ```

## MSP-Enabled Operations

| Menu | Operation | MSP Capability |
|------|-----------|----------------|
| **90** | AP Firmware Upgrade | Mode 3: Upgrade across multiple orgs |
| **116** | Org-Level AP Firmware | Mode 2: Multi-org upgrade with org-level API |
| **118** | Site Auto-Upgrade Config | Mode 2: Configure ALL sites across multiple orgs |

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

1. Run menu 115 to switch to interactive login
2. Run menu 116 (Org-Level AP Firmware Upgrade)
3. Select mode 2 (MSP Multi-Org)
4. Select MSP(s): "all" or "1,2"
5. For each MSP, select organizations: "1-10" or "all"
6. Configure upgrade settings (strategy, scheduling)
7. Confirm and execute -- upgrades run sequentially per org

## Workflow Example: Multi-Org Auto-Upgrade Configuration

1. Run menu 115 to switch to interactive login
2. Run menu 118 (Site Auto-Upgrade Configuration)
3. Select mode 2 (MSP Multi-Org)
4. Select MSP(s): "all" or "1,2"
5. For each MSP, select organizations: "1-10" or "all"
6. Configure shared schedule (day of week, time of day)
7. Each org is processed: all sites auto-selected, latest stable firmware chosen
8. Summary shows total sites configured across all orgs

## MSP Session Persistence

Once you select an MSP in menu 115, MistHelper remembers it for subsequent operations:

- Menu 116 offers your current MSP as the default
- Press Enter to use the previously selected MSP
- Or select different MSP(s) as needed

## Technical Notes

- **API Differences**: MSP operations use `mistapi.api.v1.msps.orgs.listMspOrgs()` to enumerate organizations
- **Dry-Run Support**: All MSP upgrade modes support `--dry-run` for safe validation
- **Global Variable**: MSP state stored in `msp_privileges` list and `selected_msp` dict
- **Detection Function**: `detect_msp_privileges()` called after interactive login
