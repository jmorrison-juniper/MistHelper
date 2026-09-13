# Requirements Checklist: Organization Multi-Site Firmware Upgrade

**Issue**: #2475

## Source Evidence

- [ ] CHK001 The specification names the exact organization device path.
- [ ] CHK002 The specification records the verified AP-only description.
- [ ] CHK003 The specification records the `ap`, `switch`, and `gateway`
      schema conflict.
- [ ] CHK004 The specification records the `ap` and `junos` firmware conflict.
- [ ] CHK005 The specification records the saved organization guide conflict.
- [ ] CHK006 The decision routes only APs through `upgradeOrgDevices`.

## Routing

- [ ] CHK007 The plan creates at most one organization AP child.
- [ ] CHK008 The AP child includes AP targets only.
- [ ] CHK009 Switch children use site routes from `upgrade_service.py`.
- [ ] CHK010 Junos gateway children use site routes from `upgrade_service.py`.
- [ ] CHK011 SSR children use the existing organization SSR route.
- [ ] CHK012 The gateway classifier selects Junos or SSR.
- [ ] CHK013 The planner rejects Mist Edge.

## Aggregate Model

- [ ] CHK014 One durable aggregate owns all child jobs.
- [ ] CHK015 Every child has a stable child identifier.
- [ ] CHK016 Every child stores its route and scope.
- [ ] CHK017 Every child stores its organization and site.
- [ ] CHK018 Every child stores its UI family and planned family.
- [ ] CHK019 Every child stores immutable target identifiers.
- [ ] CHK020 Every child stores status, errors, and cancellation state.
- [ ] CHK021 The aggregate survives a process restart.

## Partial and Unknown Results

- [ ] CHK022 The model keeps accepted and failed children separately.
- [ ] CHK023 The model keeps unsubmitted children separately.
- [ ] CHK024 The model keeps uncertain writes as `unknown`.
- [ ] CHK025 The model keeps uncertain cancels as `cancel_unknown`.
- [ ] CHK026 The aggregate status does not hide child detail.
- [ ] CHK027 The UI offers no retry for an unknown write.
- [ ] CHK028 Cancellation claims no firmware rollback.

## User Flow

- [ ] CHK029 The sequence is organization, mode, sites, options, confirmation,
      and progress.
- [ ] CHK030 The UI uses AP, switch, and gateway terms.
- [ ] CHK031 The confirmation page shows every child route.
- [ ] CHK032 The progress page shows every child.
- [ ] CHK033 The progress page distinguishes partial and unknown results.
- [ ] CHK034 Every driven control has a stable `data-testid`.
- [ ] CHK035 Every state appears as text and not as color alone.

## Write Safety

- [ ] CHK036 The store creates the aggregate before any cloud write.
- [ ] CHK037 The store creates every child before confirmation.
- [ ] CHK038 An atomic claim precedes each cloud write.
- [ ] CHK039 Each child has no more than one write attempt.
- [ ] CHK040 SDK retries are zero for writes.
- [ ] CHK041 Transport retries are zero for writes.
- [ ] CHK042 The service refuses a write session that permits retries.
- [ ] CHK043 A repeated submit request starts no second child write.
- [ ] CHK044 The service never retries an uncertain write.
- [ ] CHK045 Read operations alone reconcile an unknown outcome.

## Access Protection

- [ ] CHK046 The server verifies the authenticated owner.
- [ ] CHK047 The server verifies the active organization.
- [ ] CHK048 The server verifies that every site belongs to the organization.
- [ ] CHK049 The server verifies that every target belongs to a selected site.
- [ ] CHK050 The server verifies every required site lock.
- [ ] CHK051 The server verifies the stored plan hash.
- [ ] CHK052 The server verifies the exact confirmation text.
- [ ] CHK053 Every browser write includes CSRF protection.
- [ ] CHK054 Records, logs, and errors contain no credential.

## Cancellation

- [ ] CHK055 The server verifies ownership and scope before cancellation.
- [ ] CHK056 The server selects the cancel route from the stored child route.
- [ ] CHK057 An atomic cancel claim precedes each cancel write.
- [ ] CHK058 Each child has no more than one cancel attempt.
- [ ] CHK059 The service sends no automatic cancel retry.
- [ ] CHK060 Mixed cancel results remain visible.

## Offline Tests

- [ ] CHK061 Unit tests cover grouping and route selection.
- [ ] CHK062 Unit tests cover gateway classification.
- [ ] CHK063 Unit tests cover aggregate state and claims.
- [ ] CHK064 Contract tests cover every Mist child request.
- [ ] CHK065 Contract tests cover malformed answers.
- [ ] CHK066 Integration tests cover partial submission.
- [ ] CHK067 Integration tests cover unknown outcomes.
- [ ] CHK068 Integration tests cover replay prevention.
- [ ] CHK069 Integration tests cover ownership and scope failures.
- [ ] CHK070 Integration tests cover lock loss and cancellation.
- [ ] CHK071 Playwright covers the complete six-page sequence.
- [ ] CHK072 Playwright covers AP, switch, gateway, and mixed plans.
- [ ] CHK073 The socket guard blocks outbound traffic.
- [ ] CHK074 No test uses a Mist credential.
- [ ] CHK075 No test sends a live Mist write.

## Writing Quality

- [ ] CHK076 Every changed Markdown file scores 80 or more.
- [ ] CHK077 The prose uses active voice.
- [ ] CHK078 The prose uses simple tense.
- [ ] CHK079 No sentence uses a semicolon.
- [ ] CHK080 Every warning states the consequence.
