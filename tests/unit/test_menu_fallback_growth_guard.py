"""Guards against untracked growth of legacy menu fallback placeholders."""  # Define purpose so reviewers understand why this test exists.

from __future__ import annotations  # Keep postponed annotations style consistent with project modules.

import MistHelper as misthelper_package  # Import package-level menu registry surface under test.


def test_legacy_menu_placeholder_keys_are_exactly_allowed_set() -> None:  # Verify no new legacy placeholders were introduced.
    menu_actions = getattr(misthelper_package, "menu_actions", {})  # Read current menu action registry from package namespace.
    legacy_placeholder_keys: set[str] = set()  # Collect keys that still map to legacy placeholder descriptions.
    for option_key, option_value in menu_actions.items():  # Iterate menu options so we can detect placeholder descriptions.
        if not isinstance(option_value, tuple) or len(option_value) < 2:  # Skip malformed or non-standard menu entries.
            continue  # Continue scanning remaining entries without failing on unrelated shape issues.
        description_text = option_value[1]  # Extract description text used to identify placeholder entries.
        if isinstance(description_text, str) and description_text.startswith("Legacy menu option "):  # Match current placeholder marker format.
            legacy_placeholder_keys.add(str(option_key))  # Record normalized key for set-level comparison.

    allowed_legacy_keys = {str(index) for index in range(113, 188)} | {"194"}  # Define approved transitional placeholder range from compatibility contract.
    assert legacy_placeholder_keys == allowed_legacy_keys  # Fail when placeholders grow outside approved scope or unexpectedly shrink.
