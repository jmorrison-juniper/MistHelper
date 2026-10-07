# Phase-Watch Wording Contract

## Scope

This contract applies to GitHub issue #3332 Child 1 only.

It changes wording only. It does not change an upgrade request, phase gate,
watch action, lock action, or stored record.

## Required Exact Strings

The implementation must use these exact strings:

```text
The phase watch starts after the portal sends the upgrade requests.
It observes the submitted work and sends no firmware request.
It does not prove that the cloud accepted each request or that the portal sent device types in this order.
Warning: If a submission result is uncertain, do not start another upgrade. A second upgrade can target the same devices.
```

## File Contract

| File | Required contract |
| - | - |
| `src/interfaces/portals/upgrade_portal/upgrade/driver.py` | Replace the false ordered-submission promise with the first three exact strings. |
| `src/interfaces/portals/upgrade_portal/upgrade/org_cascade/walk.py` | Keep the watch read-only and use the first three exact strings. |
| `src/interfaces/portals/upgrade_portal/app/assets/templates/partials/org_phase_list.html` | Show all four exact strings to the operator. |
| `tests/contract/upgrade_portal/test_org_phase_watch_contract.py` | Directly assert all four exact strings in rendered page text. |
| `tests/unit/upgrade_portal/test_org_phase_list_parity.py` | Replace the obsolete equality assertion with exact single-site and multi-site note contracts. |
| `changelog.d/issue-3332-phase-watch-wording.md` | Describe the wording clarification and name issue #3332. |

## Direct Contract Assertion

The approved contract test must render the organization operation page. It
must normalize HTML whitespace before the text check.

The test must contain one direct assertion for each required exact string. The
assertions must use the literal strings from this contract.

The test must not replace the four assertions with:

- a selector-only check
- a partial phrase check
- a helper-only result
- a snapshot with no direct wording assertion

## Exact-String Audit

The implementation must audit all files under `tests/`.

Before the edit, search for the false promise:

```text
A phase starts only after the phase before it reports settled.
```

After the edit, search for the four required exact strings. Each new string
must occur in the approved contract test. No other test can define a different
phase-watch submission boundary.

## Excluded Contract

This contract does not define:

- settle timeout behavior
- reachability behavior
- retry behavior
- resume behavior
- firmware submission order
- lock release behavior
- durable state behavior
- route behavior

If implementation needs one of these subjects, stop and create a separate
owner decision.
