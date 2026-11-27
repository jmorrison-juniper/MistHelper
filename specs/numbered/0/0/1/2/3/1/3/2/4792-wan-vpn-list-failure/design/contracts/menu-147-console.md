# Contract: Menu 147 Console Lines

This contract defines the lines that the operator sees in menu 147. The menu is the WAN Hub-Spoke VPN Builder. Each line uses ASCII characters.

## Unavailable Inventory

When the VPN inventory is unavailable, the builder writes these lines in this order:

1. `! Error retrieving VPN definitions. Check API connectivity.` This line keeps the existing text. The level is error.
2. `  VPN creation stopped. No VPN was created. The VPN inventory could not be verified.` This line is new. The level is error.

After the second line, the builder returns. The builder shows no name prompt, no profile list, no preview, and no confirmation prompt. The menu returns to its caller.

## Verified Empty Inventory

When the VPN inventory is verified and empty, the builder keeps the existing lines:

1. `  No existing VPN definitions in this organization.` The level is warning.
2. `  Enter VPN name (or 'q' to cancel): ` is the name prompt.

## Duplicate Name

When the operator enters a name that matches a verified name, the builder keeps the existing line:

- `  VPN name '<name>' already exists. Choose a different name.` The level is warning. The builder asks for a name again.

The comparison ignores letter case and surrounding spaces (FR-014). The duplicate line uses the name that the operator entered.

## Typed Confirmation

The builder keeps the existing prompt and the existing check:

- Prompt: `  Type CREATE to confirm, or anything else to cancel: `
- Check: the operator input, after trimming, must equal `CREATE`. Any other value cancels the create path.

The change does not alter this prompt or this check (FR-015).

## Cancel and Blank Input

- The input `q` cancels the name prompt and writes `  Cancelled.`.
- A blank input writes `  VPN name cannot be empty.` and asks again.

The change does not alter these responses.
