# Analysis: Upgrade mode descriptions

**Specification**: [spec.md](spec.md)

**Plan**: [plan.md](plan.md)

**Tasks**: [tasks.md](tasks.md)

**Evidence**: [implementation.md](implementation.md)

## Requirement Coverage

| Requirement | Delivered proof |
| - | - |
| FR-001 | The real rendered pages and Chromium reject the false organization cloud job claim. |
| FR-002 and FR-003 | Both single-site descriptions name the inventory, pre-check, options, and actual site routes. |
| FR-004 and FR-005 | Both multi-site descriptions distinguish the portal operation, shared-version organization AP job, mixed-version AP site jobs, and other site routes. |
| FR-006 | Both modes name `upgradeOrgSsrs` for SSR gateways. |
| FR-007 and FR-008 | Both pages describe the newest verified standalone pre-check and the confirmation controls for missing captures. |
| FR-009 | Both pages distinguish automatic and manual post-check modes and verified comparison pairs. |
| FR-010 | The new tests retain form actions, values, CSRF fields, saved states, and navigation. Existing contracts retain typed confirmation. |
| FR-011 | Five stable description identifiers support exact browser assertions. All verified description sentences contain at most 16 words. |
| FR-012 | All 21 new cases run without a skip against offline readers and the isolated browser harness. |
| FR-013 | Both modes describe a version choice for each device that its model supports. |
| FR-014 | The browser module uses `pytest.importorskip`. The existing strict and owner tests prove both missing-package and wrong-owner failures. |
| FR-015 | Full E2E collection finds 600 cases. All six required Chromium cases pass with screenshots, tracing, and video off. |

## Consistency Review

The descriptions agree with the current services, spec 2200, and the accepted per-model repair in #3633.
The analysis does not repeat the obsolete missing-pre-check or missing-comparison statement.
The automatic post-check description applies only after the phases end and only to sites with accepted jobs.
The manual post-check description does not promise an automatic capture.

The two existing product templates contain all product changes.
The repair adds no product Python class, wrapper, API call, or stored field.
The test helpers use existing owner registration and offline readers.
The typed-confirmation templates and route modules remain unchanged.

The specification has no unresolved scope or behavior question.
Every functional requirement maps to an implementation task and verified cases.
The five specification files stay within the dedicated issue directory.

## Validation Results

The clean red run produced 13 expected description failures and eight passing control cases.
The final combined run passed 351 cases without a skip.
That run includes all 21 new cases and six real Chromium journeys.
Selection route coverage meets the 80 percent requirement at 85.55 percent.

The applicable syntax, Ruff, Black, type, Bandit, complexity, and test quality checks pass.
The complete hashed runtime audit checks 105 dependencies with zero known vulnerabilities and zero skips.
The development tools package remains outside that runtime audit because it comes from Git.
The configured STE dictionary remains unavailable, so the complete STE gate is unverified.
Native SpecKit automation also remains unavailable because this worktree has no PowerShell.
The user-authorized file-only specification process covers that automation gap.

## Delivery Status

The original local repair remains preserved.
The 2026-10-02 refresh uses only `0d1cfffbcdef3f1f66cb49b5abcfbbd3d90e0b95`.
The real route run passes 398 cases with 85.55 percent coverage.
All 21 required cases pass, including all six Chromium cases.
Full E2E collection finds 596 cases.
The full upgrade-portal run passes 327 cases and skips 52.
Of those skips, 51 require the optional journey flag and one lacks an available version in the existing capture journey.
No skipped case counts as a pass.
The six-input, three-guide preflight passes.

The current template has 23 checklist items.
Its offline review must preserve their headings, comments, text, and order.
Unavailable capabilities and inapplicable deployment actions must remain explicit.
The complete STE dictionary and licensed source remain unavailable.

The clean committed-tree analyzer and full ratchet run after the local follow-up commit.
Publication and protected merge still require the parent's separate explicit main SHA grant.
The analysis claims no push, pull request, merge, deployment, or exact-main proof.

## Authorized Publication Evidence

The parent grants the exact main revision `a11c1189d8e861bd3683e669bfdb9b654ec1eeab`.
The candidate retains the ten-file reservation and all previous local history.
Only the owned browser module changes after the rebase.
It no longer writes unconditional screenshots.
Its assertions, selectors, mode controls, model choices, and route destinations remain unchanged.

The current route proof passes 398 cases at 85.55 percent selection coverage.
All 21 owned cases pass after full E2E collection.
The full E2E run collects 600 cases, passes 548, and records the same 52 old skips.
The 139 native statistics, tier, strict, and owner checks also pass.
The required six cases create zero screenshot, trace, or video files.
The full suite retains 97 manual images from unchanged existing tests.
Those images do not change the plugin defaults and do not determine the required results.

The source-boundary proof checks 6,793 tracked paths.
It finds zero byte changes across the 6,783 unowned paths.
The 689 production Python files contain 12,458 class and function nodes and remain unchanged.
All 58 checked firmware, control, script, and shared-fixture paths also remain unchanged.

The current source gates pass with no configuration, exclusion, baseline, or suppression edit.
The fresh accepted-main CodeQL analysis has 13 existing result signatures.
Publication must compare fresh analysis results with those signatures, not claim that the baseline has no results.
The complete STE dictionary and native PowerShell capability remain unavailable.

The final merge and exact-main proof belong in the persistent PR receipt.
This pre-publication record does not claim that those later actions occurred.
