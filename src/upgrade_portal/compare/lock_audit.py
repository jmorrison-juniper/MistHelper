"""Read the append-only trail of every site lock action.

Why:
    Issue #2221 asks the history page for an audit log. `runtime/lock.py` writes
    one line for each take, release, and takeover, and this module reads them
    back for the page.

    The expiry needs no writer, and it could not have one. No request runs at the
    moment a hold ends, and the lock store drops the key, so nothing remembers
    who held the site. The reader therefore infers an expiry. A take that
    follows a take of the same site, with no release between them, means the
    earlier hold ended with no release.

Warning: the trail holds the address of each operator, because an audit trail
names people. No row that this module answers holds that address. The page shows
a one-way digest, which is the only form of an address that the portal displays.
"""

from __future__ import annotations

import json
import logging
from collections.abc import Iterator, Mapping
from typing import Any

from ..runtime.identity import email_digest
from ..runtime.lock import ACTION_EXPIRE, ACTION_TAKE, ACTION_TAKEOVER, audit_trail_path

logger = logging.getLogger(__name__)

# The largest count of rows that one read answers. The trail appends for ever,
# and a page that read the whole file would grow without bound.
DEFAULT_AUDIT_LIMIT = 200

# A row written before issue #2221 holds no action. Every such row records a
# takeover, because the takeover was the only action that the trail held.
LEGACY_ACTION = ACTION_TAKEOVER

# The two actions that open a hold on a site.
OPENING_ACTIONS = (ACTION_TAKE, ACTION_TAKEOVER)


def read_trail_lines(path: Any = None) -> Iterator[dict[str, Any]]:
    """Answer each record of the trail, oldest first.

    Why:
        A damaged line must not end the read. The trail appends, and a process
        that stopped during a write can leave a partial last line. One
        unreadable line costs the reader that line alone.

    Args:
        path: The trail file, or None for the real one.

    Yields:
        One record for each readable line.
    """
    target = audit_trail_path() if path is None else path
    try:
        with open(target, encoding="utf-8") as handle:
            for line in handle:  # One record on each line.
                text = line.strip()
                if not text:  # A blank line holds no record.
                    continue
                try:
                    record = json.loads(text)
                except ValueError:  # A partial line of an interrupted write.
                    logger.warning("audit: the trail holds one line that no reader can parse")
                    continue
                if isinstance(record, Mapping):  # A line of another shape names no action.
                    yield dict(record)
    except OSError:  # No trail exists until the first action writes one.
        logger.info("audit: the portal holds no lock trail yet")
        return


def expiry_row(earlier: Mapping[str, Any], moment: str) -> dict[str, Any]:
    """Build the row of one hold that ended with no release.

    Args:
        earlier: The record that opened the hold.
        moment: The moment of the action that found the site free.

    Returns:
        The expiry row.
    """
    return {
        "action": ACTION_EXPIRE,
        "actor_email": earlier.get("actor_email", ""),
        "previous_actor_email": "",
        "occurred_at": moment,
        "org_id": earlier.get("org_id", ""),
        "site_id": earlier.get("site_id", ""),
        "inferred": True,  # No writer recorded this row.
    }


def mark_expiries(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Add one expiry row wherever a hold ended with no release.

    Why:
        No request runs at the moment a hold ends. The lock store drops the key,
        so nothing remembers who held the site, and no writer can record the
        expiry as it happens.

        The trail states it all the same. A take that follows a take of the same
        site, with no release between them, means the earlier hold ended with no
        release.

    Args:
        rows: Every record of the trail, oldest first.

    Returns:
        The same records, with one expiry row before each take that followed an
        unreleased hold.
    """
    answered: list[dict[str, Any]] = []  # Every row that the page shows.
    holder: dict[str, dict[str, Any]] = {}  # The open hold of each site.
    for row in rows:  # One pass, oldest first, so each hold closes in order.
        site = str(row.get("site_id") or "")
        action = str(row.get("action") or LEGACY_ACTION)
        # A take of a site that still holds an open hold means the earlier hold
        # ended with no release. A takeover never reads as an expiry, because
        # the takeover row already names the operator it took the site from.
        if action == ACTION_TAKE and site in holder:
            answered.append(expiry_row(holder[site], str(row.get("occurred_at") or "")))
        answered.append(row)
        if action in OPENING_ACTIONS:  # The site now holds an open hold.
            holder[site] = row
        else:  # A release closes the hold of that site.
            holder.pop(site, None)
    return answered


def audit_row(record: Mapping[str, Any]) -> dict[str, Any]:
    """Shape one trail record into the row that the page paints.

    Warning: the row never holds an address and never holds a token. The trail
    stores the address, because an audit names people. The page shows the
    one-way digest that the portal already writes into every log record.

    Args:
        record: One record of the trail.

    Returns:
        The row, with the moment, the site, the action, and the digest.
    """
    actor = str(record.get("actor_email") or "")
    previous = str(record.get("previous_actor_email") or "")
    return {
        "action": str(record.get("action") or LEGACY_ACTION),
        "site_id": str(record.get("site_id") or ""),
        "org_id": str(record.get("org_id") or ""),
        "occurred_at": str(record.get("occurred_at") or ""),
        "actor_digest": email_digest(actor) if actor else "",
        "previous_digest": email_digest(previous) if previous else "",
        "inferred": bool(record.get("inferred", False)),
    }


def read_audit_rows(limit: int = DEFAULT_AUDIT_LIMIT, path: Any = None) -> list[dict[str, Any]]:
    """Return one page of the audit log, newest first.

    Args:
        limit: The largest count of rows to answer.
        path: The trail file, or None for the real one.

    Returns:
        One shaped row for each action, newest first.
    """
    logger.info("audit: the portal reads the site lock trail")  # Before the read.
    rows = mark_expiries(list(read_trail_lines(path)))  # Oldest first, so each hold closes in order.
    shaped = [audit_row(row) for row in reversed(rows)]  # The page reads the newest action first.
    logger.debug("audit: the trail answered %s row(s)", len(shaped))
    return shaped[:limit]
