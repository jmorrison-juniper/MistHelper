"""Guard the categories of the two operations that prompt during a sweep.

Issue #1765. Menus 195 and 196 were classified `safe`, so `--test` invoked them
unattended. Both call ``InputUtils.safe_input``. When stdin is a terminal,
``input()`` blocks and the sweep never finishes. A live run stalled for 461
seconds on menu 195 before an operator answered it.

The README defines the two read-only categories by whether they prompt:

- `safe` runs under ``--test`` and must not read stdin.
- `interactive_safe` is read-only but prompts, and runs under
  ``--testinteractive``.

Both operations are read-only, so the read-only half was right. Both prompt, so
the category was wrong.

A general static guard is not practical here. A menu handler may be a lambda
defined in ``MistHelper.py``, so the defining module of the handler is the
entrypoint itself, and the entrypoint legitimately contains many prompts. A
module-level scan would therefore flag almost every operation. The harness-level
stdin guard proposed in issue #1765 is the general answer. This test locks the
two known cases so they cannot silently regress.
"""

from __future__ import annotations  # WHY: PEP 604 unions on Python 3.10+.

import pytest  # WHY: parametrized cases keep each menu reported separately.

from src.utils.operation_registry import OperationRegistry

# Each entry is a menu that prompts, with the prompt context recorded in the log.
PROMPTING_MENUS = [
    ("195", "address_audit_csv_pick"),
    ("196", "org_license_claim_status:detail"),
]


class TestPromptingMenusAreNotSafe:
    """A menu that reads stdin must never be classified `safe`."""

    @pytest.mark.parametrize(("menu", "prompt_context"), PROMPTING_MENUS)
    def test_menu_is_not_classified_safe(self, menu: str, prompt_context: str) -> None:
        """`safe` means the sweep can run it unattended, which a prompt breaks."""
        category = OperationRegistry.skip_category(menu)
        assert category != "safe", (
            f"Menu {menu} prompts at context '{prompt_context}', so classifying it 'safe' makes "
            f"--test block on stdin. Use 'interactive_safe'. See issue #1765."
        )

    @pytest.mark.parametrize(("menu", "prompt_context"), PROMPTING_MENUS)
    def test_menu_is_interactive_safe(self, menu: str, prompt_context: str) -> None:
        """Both operations are read-only, so `interactive_safe` is the right category."""
        assert OperationRegistry.skip_category(menu) == "interactive_safe"

    @pytest.mark.parametrize(("menu", "prompt_context"), PROMPTING_MENUS)
    def test_menu_records_why_the_sweep_skips_it(self, menu: str, prompt_context: str) -> None:
        """A skip reason tells the next reader why the sweep passes the menu over."""
        reason = OperationRegistry.skip_reason(menu)
        assert reason, f"Menu {menu} needs a skip_reason naming the prompt."
