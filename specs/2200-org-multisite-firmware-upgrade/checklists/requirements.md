# Requirements Checklist: Organization Upgrade Mode for Many Sites

**Feature**: Organization upgrade mode for many sites
**Purpose**: Grade the specification and the result against the live portal
**Application**: `src/upgrade_portal` (Flask, Jinja, plain JavaScript)

## Architecture Accuracy

- [ ] CHK001 Every file anchor names a file that exists in the repository.
- [ ] CHK002 No document names `ops-portal`, React, or TypeScript as the live
      portal.
- [ ] CHK003 The documents name Flask, Jinja, and plain JavaScript.
- [ ] CHK004 The route names match `select.py`, `upgrade.py`, and
      `org_upgrade.py`.
- [ ] CHK005 The template paths match the files under `assets/templates`.
- [ ] CHK006 The session keys match the constants near line 89 of `select.py`.
- [ ] CHK007 The run states match `RunState` in `runtime/runs.py`.
- [ ] CHK008 The service names match `src/firmware/org_upgrade_service.py`.
- [ ] CHK009 The blueprint list of `factory.py` holds `org_upgrade`.

## Flow Accuracy

- [ ] CHK010 The flow starts with authentication.
- [ ] CHK011 The organization choice comes before the mode choice.
- [ ] CHK012 The mode choice comes before the site choice.
- [ ] CHK013 The pre-check capture comes before the options page.
- [ ] CHK014 The options page comes before the typed confirmation.
- [ ] CHK015 The typed confirmation comes before the organization job.
- [ ] CHK016 The poll comes after the job submission.
- [ ] CHK017 The post-check and the comparison come last.

## Mist Contract

- [ ] CHK018 The submit path is `POST /api/v1/orgs/{org_id}/devices/upgrade`.
- [ ] CHK019 The submit operation is `upgradeOrgDevices`.
- [ ] CHK020 The history operation is `listOrgDeviceUpgrades`.
- [ ] CHK021 The status operation is `getOrgDeviceUpgrade`.
- [ ] CHK022 The cancel operation is `cancelOrgDeviceUpgrade`.
- [ ] CHK023 The import path is `mistapi.api.v1.orgs.devices`.
- [ ] CHK024 The body sets `device_type` to `ap`.
- [ ] CHK025 The body sets `all_sites` to false.
- [ ] CHK026 The body uses `versions` and `site_ids`, not `version` and
      `device_ids`.
- [ ] CHK027 No document claims switch support for the organization endpoint.
- [ ] CHK028 No document claims gateway support for the organization endpoint.
- [ ] CHK029 SSR routers stay out of the first implementation.
- [ ] CHK030 Mist Edge stays out of the first implementation.
- [ ] CHK031 The portal reads the job identifier from `id`.

## API Conflicts

- [ ] CHK032 The documents record the conflict between the description and the
      device enumeration.
- [ ] CHK033 The documents record the conflict between the Markdown SDK path and
      the code import.
- [ ] CHK034 The documents record the conflict between `id` and `upgrade_id`.
- [ ] CHK035 The documents record the conflict in the peer cluster default.
- [ ] CHK036 The documents record the deprecated schedule field.
- [ ] CHK037 Each conflict row states a decision.

## Safety

- [ ] CHK038 The typed word `CONFIRM` gates every submission.
- [ ] CHK039 The server checks the word, and the browser gate alone is not
      enough.
- [ ] CHK040 The portal holds one lock for each selected site.
- [ ] CHK041 A locked site gives HTTP 409.
- [ ] CHK042 An unreachable lock store gives HTTP 503.
- [ ] CHK043 The portal releases every lock when one acquire fails.
- [ ] CHK044 The portal adds no automatic retry to any write.
- [ ] CHK045 The write session disables the SDK retry loop.
- [ ] CHK046 The write session disables the transport retry.
- [ ] CHK047 The service refuses a session that permits a retry.
- [ ] CHK048 HTTP 200 does not prove a completed upgrade.
- [ ] CHK049 A cancellation claims no rollback.
- [ ] CHK050 A malformed answer gives an error, not an empty job.
- [ ] CHK051 Every warning names the exact consequence.
- [ ] CHK052 The audit logger masks the API token.

## Pre-Checks and Comparison

- [ ] CHK053 The options page shows the pre-check state of each site.
- [ ] CHK054 A missing pre-check blocks the confirmation page.
- [ ] CHK055 The portal starts a post-check for each site.
- [ ] CHK056 The review page opens a comparison for each site.
- [ ] CHK057 A failed post-check marks one site only.

## User Interface

- [ ] CHK058 The organization pages use `portal-card` and `portal-table`.
- [ ] CHK059 The organization pages add no new color system.
- [ ] CHK060 The lock state appears as a word and not as a color alone.
- [ ] CHK061 Every driven control carries a `data-testid` attribute.
- [ ] CHK062 The confirmation field name matches between the template and the
      route of the same lane.
- [ ] CHK063 The confirmation word sits in one Jinja variable.
- [ ] CHK064 The start button carries `disabled` in the markup.
- [ ] CHK065 The browser code holds no copy of the confirmation word.
- [ ] CHK066 The progress page names every failed access point.
- [ ] CHK067 The progress page shows a true device count.

## Tests

- [ ] CHK068 Every unit test and contract test runs offline.
- [ ] CHK069 The socket block in `tests/conftest.py` stays active.
- [ ] CHK070 A test proves one cloud write for one submission.
- [ ] CHK071 A test proves that a refused body starts no cloud call.
- [ ] CHK072 A test proves that a missing word starts no cloud call.
- [ ] CHK073 A test proves that a locked site blocks the submission.
- [ ] CHK074 A test proves that a session with retries fails the write check.
- [ ] CHK075 The single-site tests pass without a change.
- [ ] CHK076 The whole portal suite runs in under 30 seconds.

## Specification Quality

- [ ] CHK077 Each requirement is testable.
- [ ] CHK078 Each user story holds acceptance scenarios.
- [ ] CHK079 Each user story holds an independent test.
- [ ] CHK080 The edge cases name a real failure mode.
- [ ] CHK081 The success criteria hold a measurable value.
- [ ] CHK082 The non-goals name the excluded families.
- [ ] CHK083 The risks name a countermeasure.
- [ ] CHK084 No requirement holds an open marker.

## Writing Quality

- [ ] CHK085 Every changed Markdown file scores 80 or more with the STE linter.
- [ ] CHK086 No sentence uses a semicolon.
- [ ] CHK087 No sentence uses a contraction.
- [ ] CHK088 No sentence uses a Latin abbreviation.
- [ ] CHK089 Every warning starts with the signal word.
- [ ] CHK090 Every instruction keeps to 20 words.

## Release Readiness

- [ ] CHK091 The seven present routes keep their behavior.
- [ ] CHK092 The two present test suites stay green.
- [ ] CHK093 The changelog names the feature.
- [ ] CHK094 The README names the access point limit.
- [ ] CHK095 The open questions of `research.md` hold answers.
- [ ] CHK096 A laboratory run proves the whole flow.
- [ ] CHK097 A reviewer confirms every non-negotiable principle.

## Notes

Grade this checklist twice. Grade it after the specification review, and grade
it again before the merge.

Warning: do not mark CHK044 without a code read, because a hidden retry can
start a second upgrade job at every selected site.
