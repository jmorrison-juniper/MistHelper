# Contract: Hardware flag environment settings

## Variables

| Variable | Default | Enabled values | Unlocks |
|----------|---------|----------------|---------|
| `PORTAL_WS_ENABLE_HARDWARE_INVENTORY` | false | `1`, `true`, `yes`, `on` | The hardware preset only |
| `PORTAL_WS_ENABLE_SHELL` | false | `1`, `true`, `yes`, `on` | The hardware preset and every free-form shell |

Enabled values come from `settings.py` line 100 (RC-124). Disabled values are an empty string, `0`, `false`, `no`, and `off` (line 102, RC-128).

## Read rule

- The reader is `StreamSettings._read_flag` (`settings.py` line 88, RC-055).
- The reader trims and lowercases the value before comparison (line 99).
- An unknown value reads false and logs one warning that names the variable (lines 104 and 105, RC-125).
- The portal reads flags once at start. A change needs a restart of the portal process.

## Stability

Variable names and defaults stay fixed by this contract. A rename needs a dated amendment to this contract.
