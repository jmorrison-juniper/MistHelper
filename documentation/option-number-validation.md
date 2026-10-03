# Upgrade option number validation

The option mapper accepts ASCII digits `0` through `9`.
A refusal names the control and does not repeat the entered value.
The refusal does not contain Python conversion advice.
Empty controls keep their existing defaults.

## Existing business ranges

| Control | Existing supported range |
| - | - |
| Failure percentage | 0 through 100 |
| First and largest radio batch percentages | 0 through 100 |
| Peer group size and parallel groups | 0 through 1000 |
| Canary phase shares | Increasing values from 1 through 100, ending at 100 |
| Single-site failure counts | Nonnegative integers without a cloud maximum |
| Organization failure counts | 0 through 2,147,483,647, enforced by the existing organization schema |
| Duration and stored seconds | 0 through the existing 41,340-second site lock horizon |
| Epoch with a clock | 120-second grace and the existing 41,340-second future window |
| Stored epoch without a clock | Nonnegative integers without a clock window |

A finite maximum determines the accepted raw digit width.
Extra leading zeros can therefore cause a representation refusal.
This is the representation change that issue #3388 requests.
The numeric value ranges do not change.
Duration units remain `s`, `m`, `h`, and `d`.
Their existing whole-number maximums are 41,340, 689, 11, and 0.
Epoch recognition still requires at least 10 digits.

## Unbounded values

Single-site failure counts and no-clock epoch replay have no supported business maximum.
The mapper does not assign either field an invented Mist API limit.
The organization failure-count maximum remains an organization rule only.

If Python enables its decimal conversion limit, the mapper checks that limit before conversion.
If Python disables its decimal conversion limit, these two fields retain unbounded conversion.
The mapper does not change the interpreter limit.
An interpreter with the limit disabled can accept a 5000-digit value in these two fields.
An isolated subprocess proves this behavior without changing the test runner.

## Current route boundary

The organization route validates failure percentages and phase shares before the mapper.
`OrgOptionRefusal.whole_number` owns that conversion in `src/upgrade_portal/app/routes/org_upgrade.py`.
The original grant contains 13 paths.
Comment 5968086205 releases only that method as the fourteenth path.
Its two production callers already use percentages with a maximum of 100.
The method rejects non-ASCII digits and raw tokens longer than three digits before integer conversion.
The unchanged shared helper rejects values above 100 before integer conversion.
Phase minimums, ordering, defaults, and organization failure-count rules remain unchanged.
Every byte outside the released method remains unchanged.

The mapper, route refusal, renderer, and browser tests use synthetic records only.
Refusal contracts measure zero plan persistence, worker, cloud-write, and firmware calls.
No test uses a production store, production port, or real firmware action.
