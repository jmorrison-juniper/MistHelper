"""Build an environment that git can parse on every developer machine.

Why:
    Git accepts configuration through three environment variables that work as
    one set: ``GIT_CONFIG_COUNT``, then ``GIT_CONFIG_KEY_n`` and
    ``GIT_CONFIG_VALUE_n`` for each index below the count. Git refuses the whole
    command when the count promises an entry that the environment does not hold.

    ``error: missing config value GIT_CONFIG_VALUE_2``
    ``fatal: unable to parse command-line config``

    The editor terminal injects that set. VS Code sends three entries, and the
    third one, ``core.fsmonitor``, carries an empty value.

Warning: on Windows an assignment of an empty string removes the variable from
the real process environment. ``os.environ['GIT_CONFIG_VALUE_2'] = ''`` leaves
the name inside the Python dictionary and drops it from the block that a child
process reads. Git then counts three entries, finds two, and stops. Any library
that saves the environment and writes it back reproduces that state, so no
single test owns the defect.

Issue #3022 records the failure. Three guards read git, passed alone, and failed
inside a full run for this reason. The guards measure tracked files and source
symbols, so the editor configuration set changes nothing they assert. This
module drops that set when it cannot survive the trip to a child process, and it
keeps the set when it is whole.
"""

from __future__ import annotations

import logging
import os

logger = logging.getLogger(__name__)  # Name the logger for this module so a reader filters by source.

CONFIG_COUNT_NAME = "GIT_CONFIG_COUNT"  # The variable that states how many entries follow.
CONFIG_KEY_PREFIX = "GIT_CONFIG_KEY_"  # The prefix of each configuration name.
CONFIG_VALUE_PREFIX = "GIT_CONFIG_VALUE_"  # The prefix of each configuration value.


def _drop_config_protocol(environment: dict[str, str]) -> dict[str, str]:
    """Return the environment without the git configuration set.

    Args:
        environment: The environment to clean.

    Returns:
        A new dict that holds no ``GIT_CONFIG_COUNT``, no ``GIT_CONFIG_KEY_n``,
        and no ``GIT_CONFIG_VALUE_n``.
    """
    return {  # WHY: one comprehension removes the whole set, because a partial set is what breaks git.
        name: value
        for name, value in environment.items()
        if name != CONFIG_COUNT_NAME
        and not name.startswith(CONFIG_KEY_PREFIX)
        and not name.startswith(CONFIG_VALUE_PREFIX)
    }


def _config_protocol_survives(environment: dict[str, str], count: int) -> bool:
    """Report whether every promised entry reaches a child process.

    Args:
        environment: The environment to inspect.
        count: The entry count that ``GIT_CONFIG_COUNT`` states.

    Returns:
        True when each index holds a name and a value that a child can read.
    """
    for index in range(count):  # WHY: git reads every index below the count, so check every one.
        key = environment.get(f"{CONFIG_KEY_PREFIX}{index}")  # The configuration name at this index.
        value = environment.get(f"{CONFIG_VALUE_PREFIX}{index}")  # The configuration value at this index.
        if not key:  # WHY: a missing name makes git stop with the same fatal error.
            return False
        if not value:  # WHY: an empty value cannot survive the trip to a child process on Windows.
            return False
    return True


def git_subprocess_environment(source: dict[str, str] | None = None) -> dict[str, str]:
    """Return an environment that git parses, for a ``subprocess`` call.

    The function keeps the editor configuration set when that set is whole. It
    drops the whole set when one entry cannot reach a child process, because git
    refuses the command in that state.

    Args:
        source: The environment to read. Leave it unset to read ``os.environ``.

    Returns:
        A new dict for the ``env`` argument of ``subprocess.run``.
    """
    environment = dict(os.environ if source is None else source)  # WHY: never mutate the caller's mapping.
    count_text = environment.get(CONFIG_COUNT_NAME)  # The variable is absent on most machines.
    if not count_text:  # WHY: no set means nothing to repair.
        return environment
    try:  # WHY: git refuses a count it cannot read, so this module drops the set instead.
        count = int(count_text)
    except ValueError:
        logger.debug("The git config count %r is not a number, so the set is dropped", count_text)
        return _drop_config_protocol(environment)
    if count < 0:  # WHY: a negative count is unusable, and git stops on it.
        logger.debug("The git config count %d is negative, so the set is dropped", count)
        return _drop_config_protocol(environment)
    if _config_protocol_survives(environment, count):  # WHY: a whole set stays, so the caller keeps editor settings.
        return environment
    logger.debug("The git config set promises %d entries that do not survive, so the set is dropped", count)
    return _drop_config_protocol(environment)
