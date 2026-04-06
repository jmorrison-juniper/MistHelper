import logging
from src.utils.prompt_logging import get_prompt_logger, log_prompt_event


def test_prompt_logging_emits():
    logger = get_prompt_logger('test_prompt')
    handler = logging.StreamHandler()
    logger.addHandler(handler)
    # Should not raise
    log_prompt_event(logger, 'test-event', {'a': 1})
    logger.removeHandler(handler)
