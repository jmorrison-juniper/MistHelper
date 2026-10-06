# Tasks: Remove safe orphan source directories

**Spec**: [spec.md](spec.md)

**Plan**: [plan.md](plan.md)

**Source Issue**: #3846

- [x] Update the sweep to count untracked candidates.
- [x] Log checked and removed counts.
- [x] Test removal of empty and cache-only directories.
- [x] Test preservation of canonical source directories and `src/__pycache__`.
- [x] Test refusal of a directory with a non-cache file.
- [x] Test measured count output.
- [x] Run all required local validation gates.
