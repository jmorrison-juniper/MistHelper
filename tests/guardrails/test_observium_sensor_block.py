"""Guardrail: the Observium sensor block cannot stop Observium when the schema is missing.

Why:
    On first boot the Observium database exists, but its tables do not. The sensor
    block runs a device lookup while Observium loads `config.php`. PHP 8 throws
    `mysqli_sql_exception` for a missing table, and the `@` operator does not
    suppress that throw. An unguarded lookup stops every Observium entry point,
    including the discovery run that creates the schema. The web UI then returns
    HTTP 500, and the syslog process restarts in a loop.

    A comment cannot hold this rule for a later edit. These tests read the script
    and fail when the lookup leaves its `try` block, or when an older block is
    appended without being removed first.
"""

from __future__ import annotations

from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
SENSOR_SCRIPT_PATH = REPOSITORY_ROOT / "container" / "observium" / "20-add-mist-static-sensors.sh"

LOOKUP = "SELECT device_id FROM devices"  # The query that throws before the schema exists.
TRY_OPEN = "try {"  # The start of the guard around the lookup.
CATCH_CLAUSE = "catch (Throwable"  # The clause that keeps a failed lookup from stopping Observium.
END_GUARD = 'grep -q "^// End MistHelper static sensors$"'  # Checks both markers before a range delete.
REMOVE_OLDER_BLOCK = "sed -i '/^\\/\\/ MISTHELPER_STATIC_SENSORS_V"  # Removes a block from an earlier version.
APPEND_BLOCK = 'cat >> "$CONFIG_PHP"'  # Appends the current block.


def script_text() -> str:
    """Read the sensor script as text.

    Returns:
        The full text of the script.
    """
    return SENSOR_SCRIPT_PATH.read_text(encoding="utf-8")


def lookup_is_guarded(text: str) -> bool:
    """Tell whether the device lookup sits inside the `try` block of the sensor block.

    Why:
        The script is shell, and the block is PHP inside a heredoc, so this check
        reads positions and does not parse PHP. The lookup must appear exactly once,
        after the `try` opener and before the `catch` clause.

    Args:
        text: The script text.

    Returns:
        True when the lookup appears once, and the three landmarks appear in order.
    """
    lookup_at = text.find(LOOKUP)
    try_at = text.find(TRY_OPEN)
    catch_at = text.find(CATCH_CLAUSE)
    in_order = 0 <= try_at < lookup_at < catch_at
    return in_order and text.count(LOOKUP) == 1


def older_block_is_removed_first(text: str) -> bool:
    """Tell whether the script removes an older block before it appends the new one.

    Why:
        A block that stays in `config.php` keeps running, and it keeps failing. The
        removal must therefore run before the append, and only after the end marker
        proves that the older block is complete.

    Args:
        text: The script text.

    Returns:
        True when the end-marker check, the removal, and the append appear in order.
    """
    guard_at = text.find(END_GUARD)
    removal_at = text.find(REMOVE_OLDER_BLOCK)
    append_at = text.find(APPEND_BLOCK)
    return 0 <= guard_at < removal_at < append_at


class TestLookupStaysGuarded:
    """The device lookup must not abort Observium before the schema exists."""

    def test_the_lookup_sits_inside_the_try_block(self) -> None:
        """A bare lookup throws on first boot, and that stops the discovery run."""
        assert lookup_is_guarded(script_text()), "The device lookup must sit between `try {` and `catch (Throwable`"

    def test_a_bare_lookup_fails_the_guard(self) -> None:
        """A script without the try opener must fail, so the guard can fail."""
        bare = script_text().replace(TRY_OPEN, "if (true) {")
        assert not lookup_is_guarded(bare)


class TestOlderBlockRemoval:
    """An older block must go before the new block is appended."""

    def test_the_older_block_is_removed_before_the_append(self) -> None:
        """Without the removal, the older failing block stays beside the new one."""
        assert older_block_is_removed_first(script_text())

    def test_an_append_without_removal_fails_the_guard(self) -> None:
        """A script that appends without the removal must fail, so the guard can fail."""
        append_only = script_text().replace(REMOVE_OLDER_BLOCK, "echo skipped # ")
        assert not older_block_is_removed_first(append_only)
