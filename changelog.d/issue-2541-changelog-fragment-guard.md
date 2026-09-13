### Release-note fragment guardrail (issue #2541)

- **Added**: `tests/guardrails/test_changelog_fragment_policy.py` reads the
  `changelog.d/` directory and the instruction files. The guard fails when a
  fragment uses a name outside the three allowed forms, when a fragment takes a
  shared name such as `unreleased.md`, when a dated name states a day that no
  calendar holds, when a fragment holds no change type, or when an instruction
  file drops the rule. Issue #2541.
