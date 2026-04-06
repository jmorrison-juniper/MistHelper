"""Input utilities for MistHelper.

Safe, testable input wrapper used by interactive prompts.
"""
from typing import Optional


class UserCancelled(Exception):
    pass


class NonInteractiveError(Exception):
    pass


class InputUtils:
    @staticmethod
    def safe_input(prompt: str, default: Optional[str] = None, allow_empty: bool = False, non_interactive_default: Optional[str] = None, interactive: bool = True) -> str:
        """Return user input or defaults.

        - interactive: when False returns non_interactive_default or default or raises NonInteractiveError.
        - handles KeyboardInterrupt by raising UserCancelled.
        """
        if not interactive:
            if non_interactive_default is not None:
                return non_interactive_default
            if default is not None:
                return default
            raise NonInteractiveError("Non-interactive and no default provided")
        try:
            raw = input(prompt)
        except KeyboardInterrupt:
            raise UserCancelled("User cancelled input")
        val = raw.strip()
        if val == "" and not allow_empty:
            return default if default is not None else ""
        return val
