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
from collections import deque
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


def mark_expiries(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:  # Preserve the existing direct inference API.
    """Add one expiry row wherever a hold ended with no release.

    Why:
        No request runs at the moment a hold ends. The lock store drops the key,
        so nothing remembers who held the site, and no writer can record the
        expiry as it happens.

        A later take of the same organization and site can identify an expiry.
        Another organization's actions cannot identify or close that hold.

    Args:
        rows: Every record of the trail, oldest first.

    Returns:
        The same records, with one expiry row before each take that followed an
        unreleased hold.
    """
    logger.info("audit: infer expiries in %s stored actions", len(rows))  # Record the ordered inference action.
    answered: list[dict[str, Any]] = []  # Retain actual actions and correctly attributed inferred expiries.
    holder: dict[tuple[str, str], dict[str, Any]] = {}  # Separate reused site text across organizations.
    for row in rows:  # One pass, oldest first, so each hold closes in order.
        organization = row.get("org_id")  # Incorrect attribution types must not equal a valid string organization.
        key = (organization if isinstance(organization, str) else "", str(row.get("site_id") or ""))  # In-memory scope.
        action = str(row.get("action") or LEGACY_ACTION)  # Preserve the legacy missing-action takeover meaning.
        # A take of a site that still holds an open hold means the earlier hold
        # ended with no release. A takeover never reads as an expiry, because
        # the takeover row already names the operator it took the site from.
        if action == ACTION_TAKE and key in holder:  # Infer only from the same organization-and-site sequence.
            answered.append(expiry_row(holder[key], str(row.get("occurred_at") or "")))  # Earlier actor, later moment.
        answered.append(row)  # An inferred expiry immediately precedes the matching actual take.
        if action in OPENING_ACTIONS:  # The site now holds an open hold.
            holder[key] = row  # A takeover replaces the matching holder without creating an immediate expiry.
        else:  # A release closes the hold of that site.
            holder.pop(key, None)  # Preserve release, explicit expiry, and other closing-action suppression.
    logger.debug("audit: expiry inference produced %s actions", len(answered))  # Report no stored address or row.
    return answered  # Keep the direct API and actual input order unchanged.


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


def _row_in_scope(record: Mapping[str, Any], org_id: str, site_id: str) -> bool:  # Require explicit organization scope.
    """Match organization and optional site before inference or result limits."""
    matches = record.get("org_id") == org_id and (  # Missing or incorrectly typed attribution cannot supply scope.
        not site_id or str(record.get("site_id") or "") == site_id  # A site narrows the organization restriction.
    )
    logger.debug("audit: the stored action matches the requested scope: %s", matches)  # Report only the safe decision.
    return matches  # Foreign records must affect neither matching hold state nor visible result positions.


def _read_limited_audit_rows(  # Retain complete matching context without retaining the whole trail.
    limit: int, path: Any = None, site_id: str = "", *, org_id: str
) -> list[dict[str, Any]]:
    """Read complete matching context and retain a bounded newest-first result."""
    logger.info("audit: read the scoped bounded lock trail")  # Record the source read and ordered inference.
    recent: deque[dict[str, Any]] = deque(maxlen=limit)  # Only matching actual and inferred rows consume positions.
    holder: dict[tuple[str, str], dict[str, Any]] = {}  # Memory follows matching open holds, not foreign events.
    for row in read_trail_lines(path):  # One pass keeps expiry inference equal to a full read.
        if not _row_in_scope(row, org_id, site_id):  # Filter before any holder or bounded-buffer update.
            continue  # Foreign and unattributed events cannot change matching inference timing or attribution.
        key = (org_id, str(row.get("site_id") or ""))  # Separate each matching organization-and-site hold.
        action = str(row.get("action") or LEGACY_ACTION)  # A record before issue #2221 holds no action.
        if action == ACTION_TAKE and key in holder:  # A matching take over an open hold identifies an expiry.
            recent.append(expiry_row(holder[key], str(row.get("occurred_at") or "")))  # Earlier actor, later moment.
        recent.append(row)  # Already scoped rows need no obsolete output-only filter.
        if action in OPENING_ACTIONS:  # A take and a takeover both open a hold.
            holder[key] = row  # Retain older matching context even when its row leaves the visible buffer.
        else:  # A release and an expiry both close the hold.
            holder.pop(key, None)  # Other sites and organizations cannot close this matching hold.
    logger.debug("audit: the scoped bounded trail retained %s rows", len(recent))  # Report only a safe count.
    logger.info("audit: shape the scoped bounded audit rows")  # Record the public-output transformation.
    shaped = [audit_row(row) for row in reversed(recent)]  # The page reads the newest action first.
    logger.debug("audit: the bounded trail answered %s rows", len(shaped))  # Never log stored audit addresses.
    return shaped  # Preserve digest-only output and bounded memory use.


def read_audit_rows(  # Require explicit organization scope with the existing positional argument order.
    limit: int | None = DEFAULT_AUDIT_LIMIT, path: Any = None, site_id: str = "", *, org_id: str
) -> list[dict[str, Any]]:
    """Read newest-first audit rows for a required organization and optional site."""
    logger.info("audit: validate the required organization scope")  # Validate before resolving or opening a trail.
    if not isinstance(org_id, str) or not org_id.strip():  # An empty or incorrectly typed scope cannot authorize input.
        logger.info("audit: refuse an invalid organization before any trail read")  # Explicit observable refusal.
        logger.debug("audit: invalid organization scope caused zero trail reads")  # Report a safe refusal summary.
        raise ValueError("The audit organization must be a nonempty string.")  # Refuse invalid scope.
    chosen = org_id.strip()  # Use the same normalized explicit organization as the history route.
    logger.debug("audit: the required organization scope is valid")  # Report no stored address or input value.
    if isinstance(limit, int) and limit > 0:  # Preserve positive bounded reads and every legacy slice meaning.
        return _read_limited_audit_rows(limit, path, site_id, org_id=chosen)  # Match before inference and limits.
    logger.info("audit: read the complete scoped lock trail")  # Record the legacy full-input source read.
    scoped = [row for row in read_trail_lines(path) if _row_in_scope(row, chosen, site_id)]  # Match before inference.
    logger.debug("audit: the complete trail matched %s actions", len(scoped))  # Report only a safe input count.
    logger.info("audit: infer and shape the complete scoped audit history")  # Record ordered output transformation.
    rows = mark_expiries(scoped)  # Foreign events cannot change matching inference state or timing.
    shaped = [audit_row(row) for row in reversed(rows)]  # Preserve newest-first digest-only output.
    answered = shaped[:limit]  # Retain the original zero, negative, and None final slice semantics.
    logger.debug("audit: the complete scoped trail answered %s rows", len(answered))  # Report no stored row content.
    return answered  # No unrestricted default organization or successful authorization fallback remains.
