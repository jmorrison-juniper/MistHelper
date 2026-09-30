"""The check of one input value against one catalog field.

Why:
    Issue #3551. The server checks every value before it sends a request to
    Mist. A refused value raises one error with a code from the HTTP contract,
    so the blueprint turns each refusal into the same JSON answer.
"""

from __future__ import annotations  # Postponed annotations keep every hint a plain string.

from collections.abc import Mapping  # Types the extra keys of a refusal.
from typing import ClassVar  # Marks the status table as one shared class value.


class StreamRequestError(Exception):
    """One refused request, with the code and the HTTP status of the contract.

    Attributes:
        code: The contract code, such as ``bad_request`` or ``limit_reached``.
        message: The plain reason for the operator.
        status: The HTTP status that the blueprint sends.
        extra: More keys for the JSON answer, such as ``field`` or ``live``.
    """

    STATUS_BY_CODE: ClassVar[dict[str, int]] = {
        "not_ready": 503,  # The portal holds no Mist session or no organization.
        "bad_request": 400,  # A field failed a check.
        "unknown_key": 404,  # The key names no catalog entry.
        "locked": 403,  # The flag of the safety class is off.
        "confirmation": 403,  # The typed device name does not match.
        "limit_reached": 429,  # The live sessions reached the limit.
        "not_found": 404,  # The session identifier names no session.
        "not_open": 409,  # The shell is not ready, or the session has ended.
        "session_live": 409,  # A delete request named a session that is still live.
    }

    def __init__(self, code: str, message: str, extra: Mapping[str, object] | None = None) -> None:
        """Build one refusal.

        Args:
            code: The contract code of the refusal.
            message: The plain reason for the operator.
            extra: More keys for the JSON answer, or None.
        """
        super().__init__(message)  # The exception text is the plain reason.
        self.code = code  # The page reads the code to pick its behavior.
        self.message = message  # The page shows this text.
        self.status = self.STATUS_BY_CODE.get(code, 400)  # An unknown code is a bad request.
        self.extra: dict[str, object] = dict(extra or {})  # A copy, so the caller cannot change it later.

    def to_payload(self) -> dict[str, object]:
        """Return the JSON answer of the refusal.

        Returns:
            The error text, the code, and each extra key.
        """
        payload: dict[str, object] = {"error": self.message, "code": self.code}  # The common error form.
        payload.update(self.extra)  # Such as the field name or the live session titles.
        return payload  # The blueprint sends this dictionary with the status.
