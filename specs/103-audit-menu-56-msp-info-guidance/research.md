# research.md

Resolved clarifications from spec (Q1..Q3)

Q1: Non-interactive behavior
- Decision: C — Accept environment variable or CLI argument for non-interactive MSP selection.
  - CLI flag: --msp-id <MSP_ID>
  - Environment variable: MISTHELPER_MSP_ID
  - Precedence: CLI flag overrides env var.

Rationale:
- Using both CLI and env var provides flexibility for both automation pipelines and ad-hoc CLI use.
- Precedence of CLI over env var matches common CLI semantics and avoids surprising behavior in scripts.

Alternatives considered:
- A: Automatically select first MSP — rejected because automation should be explicit when choosing among multiple MSPs to avoid accidental exports.
- B: Fail when multiple MSPs exist unless explicit MSP provided — viable, but more disruptive for interactive users. Chosen approach balances automation and interactive UX.

Q2: Retry policy for invalid selection
- Decision: A — Allow 3 attempts then abort.

Rationale:
- Three attempts is a common UX pattern that prevents infinite loops while giving users multiple chances to correct mistakes.
- Allows deterministic testing and simple implementation.

Alternatives considered:
- B (infinite retries) — rejected due to risk of stuck headless sessions and difficult testing.
- C (immediate abort) — rejected for being unforgiving for typos.

Q3: Short ID display
- Decision: B — display first 8 chars plus ellipsis for short id display (default). Provide --full-id to display entire id when desired.

Rationale:
- Preserves user privacy and reduces screen noise while retaining useful identifier uniqueness.
- First 8 chars is consistent with existing code behavior and minimal change risk.

Alternatives considered:
- A (full id) — verbose and may leak long IDs on screen.
- C (stable generated short id) — extra complexity for this change; can be revisited later.


Research tasks performed:
- Reviewed existing code paths in MistHelper.py for msp(), confirming current behaviors.
- Reviewed InputUtils.safe_input usage across repository to ensure dependency injection is feasible.
- Reviewed DataExporter.save_data_to_output behavior and tests to ensure CSV writing can be mocked.

Decisions summary:
- Implement MSPSelector class, add --msp-id and MISTHELPER_MSP_ID support, default retries=3, short-id display first 8 chars with --full-id override.


---

End of research.md
