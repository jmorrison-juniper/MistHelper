import pytest
from src.utils.input_utils import InputUtils, NonInteractiveError, UserCancelled


def test_safe_input_non_interactive_default():
    assert InputUtils.safe_input("prompt", non_interactive_default="def", interactive=False) == "def"
    with pytest.raises(NonInteractiveError):
        InputUtils.safe_input("p", interactive=False)


def test_safe_input_keyboard_interrupt(monkeypatch):
    def fake_input(prompt):
        raise KeyboardInterrupt
    monkeypatch.setattr("builtins.input", fake_input)
    with pytest.raises(UserCancelled):
        InputUtils.safe_input("p", interactive=True)
