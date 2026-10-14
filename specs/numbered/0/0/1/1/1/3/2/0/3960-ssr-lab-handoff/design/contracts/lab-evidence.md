# Observation Contract: SSR lab runbook validation

## Boundary

This contract defines future human evidence collection.
It does not authorize command execution during artifact preparation.
The future publication destination is `documentation/noc-runbooks/SSR_CONSOLE_HEALTH_CHECK.md`.
The [evidence model](../data-model.md) defines every required record field.

## Six Required Observations

| ID | Story | Condition and observation | Runbook destination |
| --- | --- | --- | --- |
| OBS-01 | US1 | SSR 7.0.x: run `show device-interface <name> optics-statistics` and preserve its exact result. | Section 11 error table and section 14 verification row. |
| OBS-02 | US1 | SSR 7.0.x: run `show device-interface name <name> optics-statistics` and preserve its exact result. | Section 11 error table and section 14 verification row. |
| OBS-03 | US1 | SSR 7.0.x: run `show device-interface name <name>` and compare admin status, operational status, speed, and error counters. | Step 1 of the fallback optic procedure and section 14 verification row. |
| OBS-04 | US1 | SSR 7.1.0-50r1 or later: run `show device-interface name <name> optics-statistics` on a fiber port. Record actual power and threshold field names. | Step C2 and section 14 verification row. |
| OBS-05 | US2 | Run `show mist detail` and confirm or correct the `Agent` and `Connection` field names. | Step D7 and section 14 verification row. |
| OBS-06 | US3 | Under explicit human approval, block the lab SSR cloud path on TCP port 443 and observe portal `Testing Tools`. | The last sentence of the cloud-path procedure and section 14 verification row. |

## Failure and Privacy Rules

Retain actual errors, including unexpected success or unsupported syntax.
Do not replace observed output with the expected answer.
Reject an observation that lacks its required release or port condition.
Reject published output that contains customer addresses, serial numbers, customer names, or secrets.
Keep raw evidence local in ignored `test-artifacts/issue-3960/`.
Publish only reviewed sanitized excerpts.

## Cloud-Loss Acceptance

Caution: blocking the cloud path can interrupt Mist management and require console recovery.

The human must verify the isolated lab target and independent console before the experiment.
Record explicit approval before any network change.
Record the healthy baseline and the verified loss of the agent cloud connection.
Test the portal tools only after that loss is confirmed.
If the tools operate, correct the last sentence instead of preserving an absolute failure claim.

Stop if the target is uncertain, the console fails, or an unrelated service is affected.
Restore the prior network rule through the approved recovery procedure.
Verify the agent connection returns to its baseline and record the recovery result.
Failed or unconfirmed recovery leaves OBS-06 incomplete and requires human escalation.

## Publication Contract

The later owner must check open pull requests and coordination claims before editing the runbook.
Do not edit `scripts/verify_ssr_commands.py`.
Reconcile all six section 14 rows with their actual evidence status.
Use one unique `changelog.d/issue-3960-ssr-lab-results.md` fragment for the later runbook change.
Do not close issue #3960 on artifact completion or source review alone.
