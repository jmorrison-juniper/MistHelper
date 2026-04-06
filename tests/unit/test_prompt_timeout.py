from src.input.prompt import InputPrompt


def test_inputprompt_has_timeout():
    assert hasattr(InputPrompt, "timeout")
