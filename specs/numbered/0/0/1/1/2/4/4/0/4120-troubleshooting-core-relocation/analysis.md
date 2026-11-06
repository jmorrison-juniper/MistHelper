# Relocation verification

## Specification analysis

The assessment covers seven functional requirements and 13 tasks.
All requirements have task coverage. No blocking inconsistency or unresolved ambiguity remains.

| Requirement | Tasks |
| - | - |
| FR-001 | T004, T009 |
| FR-002 | T005, T009 |
| FR-003 | T004, T005, T009 |
| FR-004 | T006, T007, T008, T011 |
| FR-005 | T007, T009, T010, T013 |
| FR-006 | T001, T003, T010 |
| FR-007 | T007, T010 |

## Structural and declaration evidence

The base is `fb7a7d10d40c89a44ccfdaf0304ec57b2fd3b02d`.
The package guard examines 182 directories and reports 33 existing violations with 236 total excess.
This result adds no violation and increases no excess.

The three moved modules retain 20, 23, and seven module-level names.
The symbol-diff comparator confirms zero additions and zero removals through explicit source-to-destination comparisons.
The CLI cannot compare renamed paths directly because those paths do not exist at the base.
The public preservation guard also compares 896 modules and 15,613 baseline symbols successfully.
Historical paths remain only in the preservation map and historical records.

## Behavior evidence

The affected unit selection passes 704 tests.
The post-annotation coverage selection passes 192 tests with 98.32 percent coverage for the moved packages.
Canonical imports, obsolete import rejection, logger identities, class identities, and both resolver entries have focused tests.
The compatibility and SDK integration selection passes ten tests.

The complete guardrail selection passes 1,114 tests and skips three tests.
Its first run lacked PowerShell on `PATH` and exposed the missing package-marker mapping.
The final run includes PowerShell and the corrected mapping.

## Static and generated evidence

- Ruff reports `All checks passed`.
- Black reports 2,544 unchanged files.
- Configured mypy reports success for 874 source files.
- Compilation passes for the entry point, resolver, and three moved modules.
- Bandit reports no finding in the moved packages.
- Pylint reports 9.92 out of ten for `src/`.
- Docstring and dead-code checks pass at their configured thresholds.
- The complexity gate reports all moved functions within ten.
- The menu generators produce no changes on their second run.
- Current open PR ownership has zero intersections with this change.

## Dependency audit environment

The standard requirements audit fails while creating its temporary environment.
Its `ensurepip` child exits with `SIGABRT`.
The direct no-dependency retry rejects the bounded `mistapi` requirement because it is not an exact pin.

The locked runtime export provides exact pins without changing repository dependency files.
The audit of that export passes with no known vulnerabilities.
The installed-environment audit also passes, but skips the two repository-owned packages absent from PyPI.

## Committed-test quality gate

The required input preflight passes with four readable, validated inputs.
The changed-test ratchet checks nine files and 27 findings with zero new findings.
The full ratchet checks 1,236 files and 585 findings with zero new findings.
The baseline remains unchanged.
