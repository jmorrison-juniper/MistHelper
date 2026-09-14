# Specification: Exclusion drift cache

## Problem
The advisory exclusion drift job runs on each pull request. The script starts many mypy processes. It also repeats the same tool run when two manifest entries use the same gate and scan path.

## Goal
Reduce the wall time for the CI command without changing the report. Keep the same exit code, result order, and finding counts.

## Non-goals
Do not add parallel work. Do not change quality gate rules. Do not change the manifest counts.

## Acceptance criteria
- The complete standard output stays identical for the measured CI arguments.
- The process exit code stays zero.
- The end-to-end median wall time improves by at least five percent.
- The subprocess launch count decreases.
