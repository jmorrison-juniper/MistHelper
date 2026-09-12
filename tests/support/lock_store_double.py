"""A stand-in for the site lock store of the upgrade portal.

Why:
    The lock rules live in `src/upgrade_portal/runtime/lock.py`, and a test must
    drive those real rules. This module stands in for the store alone, so the
    compare-and-extend and the compare-and-delete both run exactly as they run
    against Redis, with no Redis server.

    The capture start route now takes the site lock, so every test that posts a
    capture start writes a lock key. Without this stand-in that write reaches the
    Redis server of the developer machine and leaves a real key behind.

Scope:
    The three commands that `runtime/lock.py` sends: `set`, `get`, and `eval`.
    The class reads the Lua script text instead of comparing a private name, so a
    rename that changes no behavior leaves every test alone.
"""

from __future__ import annotations  # Postponed annotations keep every hint a plain string.

import json  # The stored lock value is JSON text, so the compare below decodes it.
from typing import Any  # A stored value and a script argument are both free-form.

TOKEN_FIELD = "lock_token"  # The record field that every one of the three scripts compares.
EMAIL_FIELD = "actor_email"  # The record field that names the operator who holds the site.
SCRIPT_HELD = 1  # The answer that states the script wrote or deleted.
SCRIPT_REFUSED = 0  # The answer that states the compare refused.


class FakeLockStore:
    """Answer the three store commands that the lock module sends.

    Why:
        A test needs the real lock rules and no Redis server. This class holds
        one dictionary of values and applies the same compare that the Lua
        scripts apply, so the rules above it behave as they behave in production.

    Attributes:
        values: One stored JSON text for each locked site.
        fail: True when every command must raise, which stands in for a store
            that no request can reach.
    """

    def __init__(self) -> None:
        """Start with no lock and with every command working."""
        self.values: dict[str, str] = {}  # One stored JSON value for each locked site.
        self.fail = False  # A test sets this flag to make every command raise.

    def _guard(self) -> None:
        """Raise when the test asked the store to be unreachable.

        Raises:
            ConnectionError: When the test set the failure flag.
        """
        if self.fail:  # The test asked for a store that no request can reach.
            raise ConnectionError("The stand-in lock store is down for this test.")  # The fault the caller absorbs.

    def set(self, key: str, value: str, nx: bool = False, ex: int | None = None) -> bool | None:
        """Write one value, and refuse when `nx` is set and the key exists.

        Args:
            key: The lock key.
            value: The JSON text of the record.
            nx: True when the write must fail on an existing key.
            ex: The life of the key in seconds. The stand-in expires nothing.

        Returns:
            True when the write happened, or None when `nx` refused it.
        """
        self._guard()  # A down store raises before it changes anything.
        del ex  # The stand-in holds no clock, so a test ages a record through its own timestamp.
        if nx and key in self.values:  # The `NX` flag makes the store decide the race.
            return None  # The real client answers None here, and the lock module reads that as a loss.
        self.values[key] = value  # The one place the stand-in keeps a lock.
        return True  # The caller took the lock.

    def get(self, key: str) -> str | None:
        """Read one stored value.

        Args:
            key: The lock key.

        Returns:
            The stored JSON text, or None when no lock exists.
        """
        self._guard()  # A read of a down store raises, and the page then marks the state unknown.
        return self.values.get(key)  # An absent key reads as None, never a fault.

    def eval(self, script: str, numkeys: int, key: str, *arguments: Any) -> int:
        """Run one of the three Lua scripts of the contract.

        Why:
            The three scripts share one compare and differ in what follows it.
            The stand-in reads the text for the part that differs, so a rename of
            a private constant leaves every test alone.

        Args:
            script: The Lua source the lock module sent.
            numkeys: The key count. The contract always sends one.
            key: The lock key.
            *arguments: The token, the fresh value, and the life.

        Returns:
            1 when the script wrote, or 0 when the compare refused.
        """
        self._guard()  # A down store raises, and the beat or the release then fails closed.
        del numkeys  # Every script of the contract names exactly one key.
        current = self.values.get(key)  # The value the compare reads.
        token = str(arguments[0])  # Every script compares this token first.
        if "DEL" in script:  # The release script.
            return self._compare_and_delete(key, current, token)
        if "if not current" in script:  # The refresh script, which never revives an absent key.
            return self._compare_and_write(key, current, token, arguments, revive=False)
        return self._compare_and_write(key, current, token, arguments, revive=True)  # The takeover script.

    def _compare_and_delete(self, key: str, current: str | None, token: str) -> int:
        """Delete the lock only while the caller token is the stored one.

        Args:
            key: The lock key.
            current: The stored JSON text, or None.
            token: The token the caller named.

        Returns:
            1 when the delete happened, or 0 when the compare refused.
        """
        if current is None or json.loads(current).get(TOKEN_FIELD) != token:  # A moved lock refuses.
            return SCRIPT_REFUSED  # The lock module raises `LockLostError` on this answer.
        del self.values[key]  # The site is free again.
        return SCRIPT_HELD  # The caller released its own lock.

    def _compare_and_write(self, key: str, current: str | None, token: str, arguments: Any, revive: bool) -> int:
        """Write a fresh value only while the caller token is the stored one.

        Args:
            key: The lock key.
            current: The stored JSON text, or None.
            token: The token the caller named.
            arguments: The script arguments, holding the fresh value in slot two.
            revive: True when an absent key still allows the write.

        Returns:
            1 when the write happened, or 0 when the compare refused.
        """
        if current is None:  # The lock expired between the read and the write.
            if not revive:  # A beat must never bring a dead lock back.
                return SCRIPT_REFUSED  # The lock module raises `LockLostError` on this answer.
        elif json.loads(current).get(TOKEN_FIELD) != token:  # A third party changed the lock first.
            return SCRIPT_REFUSED  # The lock module raises on this answer as well.
        self.values[key] = str(arguments[1])  # The fresh record of the caller.
        return SCRIPT_HELD  # The caller now holds the site.

    def holder_email(self, key: str) -> str:
        """Return the work email address that holds one lock.

        Why:
            A test asserts who holds a site. Reading the stored JSON here keeps
            that assertion out of every test body.

        Args:
            key: The lock key.

        Returns:
            The address of the holder, or an empty string when no lock exists.
        """
        stored = self.values.get(key)  # None means no operator holds that site.
        if stored is None:  # The site is free.
            return ""  # An empty string states that no operator holds the site.
        record: Any = json.loads(stored)  # `LockRecord.to_record` writes six flat fields.
        return str(record.get(EMAIL_FIELD, ""))  # An address of another shape reads as an empty string.
