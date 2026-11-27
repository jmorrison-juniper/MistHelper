# Lab Evidence Checklist: Issue #3392

**Purpose**: Check each posted lab answer before a branch task uses it.
**Created**: 2026-11-26
**Feature**: `design/contracts/lab-answer-record.md`

## Owner-only items

- Explained: CHK001 The owner keeps the list of lab targets outside the repository. The agent cannot check this item. Decision D-18 applies.
- Explained: CHK002 Every lab device is a lab device. The owner attests this before the first call. The agent cannot check this item.
- Explained: CHK003 Each call that reboots a device waits for a final job state before the next call to the same device (EC-4). The owner attests this item.
- Explained: CHK004 The owner repeats a check once only after a field error (EC-1). The owner keeps both answers.

## Evidence items

- [ ] CHK005 Issue #3392 holds one answer for each check ID: L-AP-STABLE, L-SSR-STABLE, L-SSR-BETA, and L-SSR-ALPHA. Checked by TST-13.
- [ ] CHK006 Each answer lists the fields of the contract in the contract order. Checked by TST-13.
- [ ] CHK007 Each answer holds no organization, site, device, router, or job identifier. Checked by TST-13.
- [ ] CHK008 Each answer holds no token, password, cookie, session value, or IP address. Checked by TST-13.
- [ ] CHK009 Each answer holds no full response body. Checked by TST-13.
- [ ] CHK010 The access point answer names the job read getOrgDeviceUpgrade (RC-114).
- [ ] CHK011 Each router answer names the job read listOrgSsrUpgrades (RC-115) and does not name getOrgSsrUpgrade (RC-117).
- [ ] CHK012 Each job status word is one word of the enum at lines 115749 to 115760 (RC-78).
- [ ] CHK013 Each verdict follows the first verdict rule that fits (V-1, V-2, or V-3) in the contract.
- [ ] CHK014 Each router answer names one router. A split result follows EC-3 and marks the value as refused.
- [ ] CHK015 The verdicts match the branch chosen in tasks T011 to T015.
