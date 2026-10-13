"""Guard the policy for automatic Companion progress updates."""

from pathlib import Path
from typing import Any

import yaml

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]  # Locate the repository from this guard.
EXTENSIONS_PATH = REPOSITORY_ROOT / ".specify" / "extensions.yml"  # Read the configured hooks.
EXPECTED_COMMANDS = {  # Keep the complete set of progress-writing actions explicit.
    "speckit.companion.after-specify",
    "speckit.companion.after-plan",
    "speckit.companion.after-tasks",
    "speckit.companion.after-implement",
    "speckit.companion.before-converge",
    "speckit.companion.after-converge",
}


class TestCompanionProgressHooks:
    """Check that automatic Companion progress updates stay disabled."""

    @staticmethod
    def companion_hook_policy_is_valid(companion_hooks: dict[str, Any]) -> bool:
        """Reject missing or enabled progress actions."""
        has_expected_actions = set(companion_hooks) == EXPECTED_COMMANDS  # Keep the configured action set fixed.
        all_actions_disabled = all(  # Prevent automatic writes to tracked progress records.
            hook.get("enabled") is False for hook in companion_hooks.values()
        )
        return has_expected_actions and all_actions_disabled  # Require both policy conditions.

    def test_progress_hooks_are_disabled(self) -> None:
        """Reject missing or enabled progress hooks before they dirty tracked files."""
        document: dict[str, Any] = yaml.safe_load(  # Parse the authoritative project configuration.
            EXTENSIONS_PATH.read_text(encoding="utf-8")
        )
        hooks: dict[str, list[dict[str, Any]]] = document["hooks"]  # Read every lifecycle hook.
        companion_hooks = {  # Find every configured Companion action.
            hook["command"]: hook
            for hook_list in hooks.values()
            for hook in hook_list
            if hook.get("extension") == "companion"
        }

        assert self.companion_hook_policy_is_valid(companion_hooks)  # Enforce the complete disabled policy.

    def test_policy_rejects_enabled_or_missing_actions(self) -> None:
        """Prove that the regression check rejects unsafe configuration changes."""
        disabled_hooks = {  # Represent the expected disabled configuration.
            command: {"enabled": False} for command in EXPECTED_COMMANDS
        }
        enabled_hooks = dict(disabled_hooks)  # Isolate the simulated hook change.
        enabled_hooks["speckit.companion.after-specify"] = {"enabled": True}  # Simulate an unsafe action.
        missing_hooks = dict(disabled_hooks)  # Isolate the simulated hook removal.
        missing_hooks.pop("speckit.companion.after-specify")  # Simulate a missing required action.

        assert not self.companion_hook_policy_is_valid(enabled_hooks)  # Reject an enabled progress action.
        assert not self.companion_hook_policy_is_valid(missing_hooks)  # Reject a missing progress action.
