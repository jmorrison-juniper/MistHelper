# Tasks: MistHelper.py Suppression Cleanup

**Issue**: #1004

## Implementation Tasks

- [x] 1. Read the existing specification files in `specs/1016-misthelper-suppression-cleanup/`.
- [x] 2. Run the suppression search against `MistHelper.py`.
- [x] 3. Run `ruff check MistHelper.py --select ALL --statistics` and record the current tool signal.
- [x] 4. Update `spec.md` so it states the current truth.
- [x] 5. Update `plan.md` with the concrete repair plan.
- [x] 6. Replace the direct `subprocess` import with an audited subprocess import path.
- [x] 7. Replace the PyPI `urlopen` call with a bounded `requests.get` call.
- [x] 8. Replace untyped optional `paramiko` imports with dynamic imports.
- [x] 9. Replace the dynamic `mistapi` attribute write with a dictionary binding.
- [x] 10. Replace the hardcoded bind-all literal with a guarded runtime value.
- [x] 11. Update the bind-address guardrail tests for the no-suppression rule.
- [x] 12. Add the issue #1004 release note fragment.
- [x] 13. Run the local quality gates and record evidence in `analysis.md`.
- [x] 14. Add `analysis.md` with the final evidence.
