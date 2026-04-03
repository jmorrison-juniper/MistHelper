# Implementation Plan: MSP info guidance (Audit)

Branch: 103-audit-menu-56-msp-info-guidance
Spec: specs/103-audit-menu-56-msp-info-guidance/spec.md

## 1) Summary mapping to acceptance criteria

This plan implements the audit fixes for MistHelper Menu #56 (function msp in MistHelper.py) to satisfy the spec's Acceptance Criteria (AC-001..AC-005). In short:

- FR-001 / AC-001: Preserves and stabilizes the guidance output when msp_privileges is falsy; guidance text moved to constants and covered by unit tests.
- FR-002 / AC-002: Replace one-shot prompt with an MSPSelector class that presents a numbered list, shows the valid numeric range, accepts numeric input, retries up to 3 times, handles KeyboardInterrupt/EOF, and supports non-interactive selection via CLI flag or env var.
- FR-003 / AC-003: Add pre-call validation for apisession and strong response validation (has .data, list-like, dict records); malformed records are logged and sanitized/omitted.
- FR-004 / AC-004: Replace broad exception catch with targeted exceptions and ensure logged tracebacks while presenting concise user messages and returning documented non-zero statuses.
- FR-005 / AC-006: Export includes msp_id and msp_name; summary output safely truncates IDs to first 8 chars with ellipsis by default, with --full-id option override.

This plan produces: plan.md, research.md, data-model.md, quickstart.md, tasks.md in the spec directory and code changes described below.

## 2) Concrete refactor plan (small class-based change)

Design decision: implement a small MSPSelector class in src/msp/selector.py that encapsulates selection logic and validation. Keep class < 5 methods where possible to follow the Five-Item Rule.

Class signature (suggested):

class MSPSelector:
    def __init__(self, msp_privileges: Sequence[dict], input_fn: Callable[[str], str] = None, retries: int = 3, non_interactive_choice: Optional[str] = None):
        """msp_privileges: list of {'msp_id','msp_name','role'}
        input_fn: injectable input function for testing (defaults to InputUtils.safe_input)
        retries: number of attempts for interactive input
        non_interactive_choice: MSP id provided via CLI flag or env var
        """

    def choose(self) -> dict:
        """Returns the chosen MSP dict (with keys: msp_id, msp_name)
        Raises: ValueError on invalid non-interactive choice, KeyboardInterrupt on interrupt, RuntimeError on abort after retries
        """

    def _format_list(self) -> List[str]:
        """Return formatted lines for display"""

    def _parse_choice(self, choice_str: str) -> int:
        """Parse and validate numeric choice, raising ValueError on invalid"""

Minimal patch examples (apply conceptually; tests will validate):

- New file: src/msp/selector.py (new module)
  - Implements MSPSelector as above; uses InputUtils.safe_input by default via dependency injection.

- MistHelper.py (minimal changes):
  - Replace in-function selection block with:

      from src.msp.selector import MSPSelector

      selector = MSPSelector(msp_privileges, input_fn=InputUtils.safe_input, retries=3, non_interactive_choice=cli_args.msp_id or os.environ.get('MISTHELPER_MSP_ID'))
      try:
          chosen = selector.choose()
      except KeyboardInterrupt:
          print("X Selection aborted by user")
          return EXIT_NON_ZERO
      except RuntimeError as e:
          print(f"X {e}")
          return EXIT_NON_ZERO

  - Continue with apisession check and API call as before, using chosen['msp_id'] and chosen['msp_name'].

Patch example (diff-like pseudocode):

- Old (excerpt):
-    choice = InputUtils.safe_input("  Select MSP (number): ", context="msp_export")
-    try:
-        idx = int(choice) - 1
-    except ValueError:
-        print("X Invalid input")
-        return
+ New (excerpt):
+    selector = MSPSelector(msp_privileges, input_fn=InputUtils.safe_input, retries=3, non_interactive_choice=cli_args.msp_id or os.environ.get('MISTHELPER_MSP_ID'))
+    chosen = selector.choose()

Notes on keeping methods small: MSPSelector._parse_choice and _format_list extracted so choose() stays small.

## 3) Non-interactive API: CLI flag and environment variable

Design:
- CLI flag: --msp-id <MSP_ID>
- Environment variable: MISTHELPER_MSP_ID
- Precedence: CLI flag takes highest precedence, then env var.
- Validation: If non-interactive choice provided and it matches an msp in msp_privileges, select it. If it does not match, error with message "Specified MSP id '<value>' not found; available ids: <list_short>" and exit non-zero.
- If non-interactive choice is absent and multiple MSPs exist, selection is interactive per normal flow. Optionally, a --non-interactive flag could force failure instead of prompting; we will implement the simpler precedence behavior and add TODO to extend.

CLI help example (usage excerpt):

  --msp-id MSP_ID        Select MSP non-interactively (takes precedence over MISTHELPER_MSP_ID env var)
  --full-id              Show full organization IDs in summary output (default shows first 8 chars)

Unit tests to add (names):
- test_cli_msp_id_precedence_over_env
- test_env_msp_id_selection
- test_nonexistent_msp_id_errors

## 4) Retry policy and KeyboardInterrupt handling

- Default retries: 3 (per provided choice Q2: A).
- Behavior: On invalid numeric input (non-integer or out-of-range), print message: "X Invalid selection — enter a number between 1 and {N} (attempt {i}/{retries})" and prompt again until attempts exhausted. On 3 invalid attempts, raise RuntimeError("Too many invalid attempts; aborting") which MistHelper.py will catch and print a short message and return documented non-zero status.
- KeyboardInterrupt / EOF: bubble as KeyboardInterrupt; MistHelper.py will handle by printing "X Selection aborted by user" and returning documented non-zero status.

## 5) Output formatting (Q3 resolved)

Decision (Q3: B): display truncated ID as first 8 characters + '...' by default. Provide --full-id CLI flag to override and display full ID. Use safe transformation: short = (str(org_id)[:8] + '...') if org_id else '(missing-id)'.

## 6) Tests (unit & integration)

Unit tests (directory: tests/unit/):
- test_no_msp_privileges_shows_guidance (TC-001)
- test_single_msp_auto_selects_and_exports (TC-002)
- test_multiple_msps_valid_selection_exports (TC-003)
- test_invalid_selection_retry_and_abort (TC-004)
- test_keyboard_interrupt_during_selection (TC-005)
- test_apisession_none_reports_error (TC-006)
- test_api_returns_empty_list_creates_empty_csv (TC-007)
- test_api_returns_malformed_data_handles_gracefully (TC-008)
- test_data_processing_adds_msp_context (TC-009)
- test_export_io_error_logged_and_reported (TC-010)
- test_cli_msp_id_precedence_over_env
- test_env_msp_id_selection

Integration tests (tests/integration/):
- integration_test_msp_export_end_to_end (mock mistapi and DataExporter to verify invocation chain)

Mocking guidance:
- Inject input_fn for MSPSelector tests.
- Patch mistapi.v1.msps.orgs.listMspOrgs to return dummy response objects with .data.
- Patch DataExporter.save_data_to_output to capture call args and avoid disk IO.

CI steps (in tasks.md): run unit tests via pytest, run flake8/pycompile, run selected integration tests.

## 7) Tasks (see tasks.md for full dependency-ordered list)

(See specs/103-audit-menu-56-msp-info-guidance/tasks.md)

## 8) Assumptions and human review items

Assumptions:
- InputUtils.safe_input behaves like built-in input but may raise KeyboardInterrupt/EOFError.
- DataExporter API remains unchanged and supports being patched in tests.
- MistAPI response objects follow pattern: response.data

Human review required:
- Confirm desired exit codes for automation: we return standard 2 for user abort, 3 for validation failure, 4 for API/IO errors. If product requires different codes, update plan.
- Decide whether to add a --non-interactive flag that forces failure when multiple MSPs exist (future work).


---

End of plan.md
