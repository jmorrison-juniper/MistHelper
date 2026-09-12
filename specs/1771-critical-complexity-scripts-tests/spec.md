# Feature Specification: Critical Complexity in scripts/ and tests/ (#1771)

**Branch**: `refactor/1771-critical-complexity-scripts-tests`
**Created**: 2026-08-05
**Issue**: <https://github.com/jmorrison-juniper/MistHelper/issues/1771>
**Status**: Specified. Implementation not started.

## Problem / Goal

Three symbols carry critical cyclomatic complexity. All three sit in areas that
no gate and no earlier spec covered.

| Symbol | Location | Complexity | Target |
| - | - | - | - |
| `summarize` | `scripts/analyze_marvis_pcap.py:26` | 49 | <= 5 |
| `test_v2_cache_promotes_to_v3_shape_in_memory` | `tests/unit/utils/test_zscaler_catalogue.py:509` | 49 | <= 5 |
| `_render_section` | `scripts/probe_zscaler_endpoints.py:191` | 21 | <= 5 |

They became visible on 2026-08-05, when the compliance analyzer first ran across
the whole repository instead of `MistHelper.py` and `src` alone.

### Goal

Bring all three to a complexity the analyzer accepts, and decide whether the CI
radon gate should cover the areas that hid them.

### Non-goals

- The 297 high-severity findings. Specs 1008 and 1009 already hold that backlog.
- Any behavior change. Each symbol must produce the same output as before.

## Why this is not already covered

Spec `433-full-repo-compliance-sweep` set "5 critical violations to 0" as its
Target D. Issue #433 is closed and its other targets are met:

| Target | Then | Now |
| - | - | - |
| `src/firmware/site_auto_upgrade.py` | 27 / F | 100.0 / A+ |
| `src/maps/maps_manager.py` | 40 / F | 100.0 / A+ |

The `src/` work landed. These three were never in scope, because at the time
nothing analyzed `scripts/` or `tests/`.

## Interfaces & Behavior

No public interface changes. `summarize` and `_render_section` are internal to
their scripts. The test keeps its name, or splits into named cases.

## Constraints

- Output must not change. `summarize` and `_render_section` build reports that a
  reader compares between runs.
- The 5-Item Rule applies to every helper this work extracts.
- The test case must stay deterministic.

## Test Plan

1. Capture the current output of both scripts on a fixed input. Compare byte for
   byte after the refactor.
2. Run the existing `test_zscaler_catalogue.py` suite before and after. The same
   assertions must hold.
3. Re-run the compliance analyzer repository-wide. Confirm 0 critical findings.

## Open Questions

1. Should the CI radon gate extend past `src/`? Without that, these can regress
   silently. The gate currently runs `radon cc src/`.
2. The test at complexity 49 branches 49 ways in one case. Split into separate
   cases, or parametrize? A reader cannot currently tell which path ran when it
   passes.
3. Are `scripts/` and `tests/` held to the same 5-Item Rule as `src/`? The
   analyzer applies it. No written decision records whether that is intended.

## Acceptance Criteria

- [ ] All three symbols report complexity <= 10, ideally <= 5.
- [ ] The analyzer reports 0 critical STRUCT-COMPLEXITY findings repo-wide.
- [ ] Script output is unchanged, proven by a captured comparison.
- [ ] A recorded decision on the radon gate scope.

## Next Step

Run `speckit.plan`. Question 1 and question 3 need an answer before the task
list can be written, because they decide whether this is a three-symbol fix or
the first slice of a wider policy change.
