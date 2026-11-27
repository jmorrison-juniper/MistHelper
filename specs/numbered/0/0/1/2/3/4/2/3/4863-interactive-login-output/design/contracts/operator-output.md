# Contract: Interactive Login Console Output

This contract lists every line that the interactive login prints after this change. It covers the `--login` startup path and the switch to interactive login (menu 143). Each line is ASCII text, in plain words for a junior NOC engineer. The line numbers cite the remote file of `main` (`design/research.md`, RC rows).

## Identity

- Startup path: `establish_mist_session` calls `_init_interactive_session` in `MistHelper.py`. The session comes from `LoginOrchestrator.execute`.
- Switch path: menu 143 runs `SwitchToInteractiveLoginManager.run`. That path adds the banner, the confirmation, the MSP picker, and the organization picker.
- Status values: `unchanged` means the text and the channel do not change. `converted` means the text stays and the channel changes. `new` means the line is added.

## Direct output

Direct output prints to the terminal without a log label. Each row lists the order, the phase, the exact text, the source line, and the status. Angle brackets mark a run value, such as a name or a count. The operator sees the actual value.

| Order | Phase | Text | Source | Status |
|-------|-------|------|--------|--------|
| 1 | Cloud menu | Blank line | `clouds.py` 66 | converted |
| 2 | Cloud menu | A line of 60 equal signs | `clouds.py` 67 | converted |
| 3 | Cloud menu | `  INTERACTIVE MIST API LOGIN` | `clouds.py` 68 | converted |
| 4 | Cloud menu | A line of 60 equal signs | `clouds.py` 69 | converted |
| 5 | Cloud menu | Blank line | `clouds.py` 70 | converted |
| 6 | Cloud menu | `  This authentication method uses session/cookie-based login,` | `clouds.py` 71 to 73 | converted |
| 7 | Cloud menu | `  which can access MSP-level APIs (unlike org-scoped API tokens).` | `clouds.py` 74 to 76 | converted |
| 8 | Cloud menu | Blank line | `clouds.py` 77 | converted |
| 9 | Cloud menu | `  Available Mist Clouds:` | `clouds.py` 78 | converted |
| 10 | Cloud menu | One row for each cloud: number, name, and host | `clouds.py` 80 | converted |
| 11 | Cloud menu | Blank line | `clouds.py` 81 | converted |
| 12 | Cloud prompt | `  Select cloud (1-11, or press Enter for Global 01): ` | `clouds.py` prompt | unchanged, safe input |
| 13 | Cloud choice | `  Using cloud: <name> (<host>)` | `clouds.py` 58 | unchanged, already `echo` |
| 14 | Cloud choice | Blank line | `clouds.py` 59 | converted |
| 15 | Email prompt | `  Email: ` | `credential_prompter.py` prompt | unchanged, safe input |
| 16 | Password prompt | `  Password: ` with hidden input | `credential_prompter.py` prompt | unchanged, masked input |
| 17 | 2FA banner | Blank line | `login_orchestrator.py` 191 | converted |
| 18 | 2FA banner | `  Two-factor authentication required.` | `login_orchestrator.py` 192 | converted |
| 19 | 2FA prompt | `  Enter 2FA code: ` | `credential_prompter.py` prompt | unchanged, safe input |
| 20 | 2FA success | `  + 2FA verification successful` | `login_orchestrator.py` after 204 | new |
| 21 | Login success | Blank line | `login_orchestrator.py` 229 | converted |
| 22 | Login success | `  + Login successful!` | `login_orchestrator.py` 230 | converted |
| 23 | MSP summary | `  + MSP access detected: <n> MSP(s) available` | `login_orchestrator.py` 242 | converted |
| 24 | MSP summary | `    - <name> (role: <role>)`, one row for each MSP | `login_orchestrator.py` 246 | converted |
| 25 | MSP summary | `  - No MSP privileges detected (org-level access only)` | `login_orchestrator.py` 248 | converted |
| 26 | MSP summary | Blank line | `login_orchestrator.py` 249 | converted |
| 27 | MSP picker | Blank line, a line of 60 equal signs, `  SELECT MSP AND ORGANIZATION`, a line of 60 equal signs, and a blank line | `msp_org_selector.py` 45 to 49 | converted |
| 28 | MSP picker | `  Using MSP: <name> (only one available)` | `msp_org_selector.py` 55 | converted |
| 29 | MSP picker | `  Available MSPs:`, then one numbered row for each MSP | `msp_org_selector.py` 88 and 92 | converted |
| 30 | MSP picker | `  Select MSP (number, or Enter to skip): ` | `msp_org_selector.py` prompt | unchanged, safe input |
| 31 | MSP picker | `  Skipping MSP selection - using direct org access` | `msp_org_selector.py` 72 | converted |
| 32 | MSP picker | `  + Selected MSP: <name>` | `msp_org_selector.py` 100 | converted |
| 33 | Organization picker | `  Found <n> organization(s):`, one numbered row for each organization, and a blank line | `msp_org_selector.py` 137 and 138 | converted |
| 34 | Organization picker | `  Enter number to select, or 'q' to skip` | `msp_org_selector.py` 195 | converted |
| 35 | Organization picker | `  Selection: ` | `msp_org_selector.py` prompt | unchanged, safe input |
| 36 | Organization picker | `  Skipping org selection` | `msp_org_selector.py` 206 | converted |
| 37 | Organization picker | `  + Selected organization: <name>` and `  + Organization ID: <id>` | `msp_org_selector.py` 228 and 229 | converted |
| 38 | Organization picker | `  No organizations found under this MSP` | `msp_org_selector.py` 133 | converted |

The multi-page hint in `_render_page` is not reached, because the picker always uses one page. Its three lines convert with the same rule.

## Failure lines (warning or error records)

Failure lines keep their level. Each one carries an `X` marker, and the operator sees a label from the console handler.

| Text | Source | Record |
|------|--------|--------|
| `X Failed to import mistapi library` | `login_orchestrator.py` 58 | warning |
| `  X Failed to create API session` | `login_orchestrator.py` 147 | warning |
| `  X Authentication failed: <message>` | `login_orchestrator.py` 222 | warning, and an error record |
| `  X Connection failed: <message>` | `login_orchestrator.py` 253 | warning |
| `  X Invalid API token or credentials` | `login_orchestrator.py` 262 | warning |
| `  X Authentication error: <message>` | `login_orchestrator.py` 264 | warning |
| `  X Invalid email or password` | `login_orchestrator.py` 286 | warning |
| `  X Two-factor authentication failed` | `login_orchestrator.py` 289 | warning |
| `  X Invalid email or password (authentication failed)` | `login_orchestrator.py` 292 | warning |
| `  X Login failed: <message>` | `login_orchestrator.py` 294 | warning |
| `X Email is required` | `credential_prompter.py` 28 | warning |
| `X Failed to read password: <message>` | `credential_prompter.py` 44 | warning |
| `X Password is required` | `credential_prompter.py` 47 | warning |
| `  X 2FA code is required` | `credential_prompter.py` 62 | warning |
| `  X Invalid input - skipping MSP selection` | `msp_org_selector.py` 69 | warning |
| `  X Invalid selection - skipping MSP selection` | `msp_org_selector.py` 77 and 80 | warning |
| `  X API session not initialized` | `msp_org_selector.py` 104 | warning |
| `  X Error fetching MSP organizations: <message>` | `msp_org_selector.py` 110 | warning |
| `  X Failed to retrieve MSP organizations` | `msp_org_selector.py` 126 | warning |
| `  X Invalid input - try again` | `msp_org_selector.py` 215 | warning |
| `  X Invalid number - try again` | `msp_org_selector.py` 219 | warning |

## Info records (file log, and terminal at threshold 20 or lower)

| Message (text) | Source | Record |
|----------------|--------|--------|
| `Authenticating to <host> as <email> on cloud <name>` | `login_orchestrator.py` 84 | info, unchanged |
| `Creating mistapi APISession for <host>` | `login_orchestrator.py` 137 | info, unchanged |
| `Sending initial login_with_return() request` | `login_orchestrator.py` 170 | info, unchanged |
| `Resubmitting login_with_return() with 2FA code` | `login_orchestrator.py` 198 | info, unchanged |
| `Running detect_msp_privileges callback` | `login_orchestrator.py` 237 | info, unchanged |
| The organization progress line for the MSP name | `msp_org_selector.py` 101 | info, converted |
| `User cancelled switch to interactive login` | `MistHelper.py` 2702 | info, converted |

## Removed lines

These progress lines are deleted. Each one duplicated an info record that stays.

- `login_orchestrator.py` 85: blank spacer before the authentication progress line.
- `login_orchestrator.py` 86: authentication progress line. Duplicates line 84.
- `login_orchestrator.py` 136: APISession progress line. Duplicates line 137.
- `login_orchestrator.py` 169: login request progress line. Duplicates line 170.
- `login_orchestrator.py` 197: 2FA resubmission progress line. Duplicates line 198.
- `login_orchestrator.py` 236: MSP check progress line. Duplicates line 237.

## Rules

- The order of direct output lines does not change.
- A secret never appears in a line. Passwords and 2FA codes are never printed, logged, or stored in a message.
- The SDK prints no info line in this sequence at console level 30. An SDK error line still prints.
