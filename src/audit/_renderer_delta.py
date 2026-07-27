"""Delta / diff computation helpers for :mod:`src.audit.renderer`.

This module owns the recursive dict/list delta engine used by the
Mermaid and HTML rollback reports. It was split out of ``renderer.py``
to isolate the algorithm from I/O-oriented rendering code and to keep
each helper under the 5-block / cc<=5 / 25-line compliance budget.
Public entry points are re-exported by :class:`AuditReportRenderer`
as ``@staticmethod`` bindings so external test call sites continue to
work unchanged.
"""

from __future__ import annotations  # WHY: postponed evaluation for forward-ref type hints

from dataclasses import dataclass  # WHY: bundle 5 diff-key inputs into a struct (STRUCT-PARAMS fix)
from typing import Any  # WHY: broad payload typing for arbitrary audit JSON shapes

# WHY: ordered identity-candidate keys tried when matching list elements
_IDENTITY_KEYS: tuple[str, ...] = ("name", "id", "ssid", "network_id", "servicepolicy_id")  # WHY: id priority


@dataclass(frozen=True)  # WHY: immutable bundle keeps diff_key signature <=5 params
class DiffKeyContext:  # WHY: exported for tests binding on AuditReportRenderer
    """Bundle inputs for :func:`diff_key` to keep the signature <=5 params.

    ``in_before`` / ``in_after`` explicitly track dict membership so that
    a legitimate ``None`` value (versus a missing key) is still emitted
    into the delta output for the side that actually contained the key.
    """

    key: str  # WHY: dict key being diffed
    val_b: object  # WHY: value on the 'before' side (may be None-legit)
    val_a: object  # WHY: value on the 'after' side (may be None-legit)
    in_before: bool  # WHY: distinguishes explicit None from a missing key
    in_after: bool  # WHY: distinguishes explicit None from a missing key


def compute_delta(
    before: dict[str, Any],
    after: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:  # WHY: public entry point re-exported from renderer
    """Extract only the fields that differ between ``before`` and ``after``."""
    empty = _empty_side_delta(before, after)  # WHY: fast-path when at least one side is empty
    if empty is not None:  # WHY: skip full walk when we already know the answer
        return empty  # WHY: propagate shortcut result unchanged
    delta_b: dict[str, Any] = {}  # WHY: accumulate 'before' side of the diff
    delta_a: dict[str, Any] = {}  # WHY: accumulate 'after' side of the diff
    all_keys = set(list(before.keys()) + list(after.keys()))  # WHY: union covers both sides
    for key in sorted(all_keys):  # WHY: deterministic key order for reproducible output
        _accumulate_key_delta(key, before, after, delta_b, delta_a)  # WHY: per-key dispatch keeps CC low
    return delta_b, delta_a  # WHY: paired dicts describe both sides of the diff


def _empty_side_delta(
    before: dict[str, Any],
    after: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]] | None:  # WHY: returns None when caller must run full walk
    """Return the shortcut delta pair when one/both sides are empty."""
    if not before and not after:  # WHY: nothing on either side -> no diff to report
        return {}, {}  # WHY: two empty dicts represent 'no diff'
    if not before:  # WHY: everything in 'after' is new
        return {}, after  # WHY: signal every key was added
    if not after:  # WHY: everything in 'before' is removed
        return before, {}  # WHY: signal every key was removed
    return None  # WHY: signal caller to run the general walk


def _accumulate_key_delta(
    key: str,
    before: dict[str, Any],
    after: dict[str, Any],
    delta_b: dict[str, Any],
    delta_a: dict[str, Any],
) -> None:  # WHY: mutates delta dicts in place to keep compute_delta short
    """Diff a single dict key in place, extending the running deltas."""
    val_b = before.get(key)  # WHY: shared for equality check and dispatch
    val_a = after.get(key)  # WHY: shared for equality check and dispatch
    if val_b == val_a:  # WHY: identical values contribute nothing to the delta
        return  # WHY: early exit skips context construction cost
    ctx = DiffKeyContext(  # WHY: bundle 5 inputs for the delegated diff routine
        key=key,
        val_b=val_b,
        val_a=val_a,
        in_before=key in before,
        in_after=key in after,
    )
    diff_key(ctx, delta_b, delta_a)  # WHY: recursive/scalar dispatch owned by diff_key


def diff_key(
    ctx: DiffKeyContext,
    delta_b: dict[str, Any],
    delta_a: dict[str, Any],
) -> None:  # WHY: exported via staticmethod binding on renderer for tests
    """Diff one key's values, dispatching on type."""
    if isinstance(ctx.val_b, dict) and isinstance(ctx.val_a, dict):  # WHY: recurse into nested dicts
        diff_key_dict(ctx.key, ctx.val_b, ctx.val_a, delta_b, delta_a)  # WHY: dict branch delegates to nested walker
        return  # WHY: consumed by nested walker. Skip remaining dispatch
    if isinstance(ctx.val_b, list) and isinstance(ctx.val_a, list):  # WHY: recurse into nested lists
        diff_key_list(ctx.key, ctx.val_b, ctx.val_a, delta_b, delta_a)  # WHY: identity-aware list walker
        return  # WHY: consumed by list walker. Skip remaining dispatch
    _emit_scalar_delta(ctx, delta_b, delta_a)  # WHY: mixed/scalar path emits raw values


def _emit_scalar_delta(
    ctx: DiffKeyContext,
    delta_b: dict[str, Any],
    delta_a: dict[str, Any],
) -> None:  # WHY: side effects only. Writes into caller-owned dicts
    """Emit scalar or mixed-type value into the delta dicts."""
    if ctx.in_before:  # WHY: preserve explicit None distinct from absent
        delta_b[ctx.key] = ctx.val_b  # WHY: record before-side value even if None
    if ctx.in_after:  # WHY: preserve explicit None distinct from absent
        delta_a[ctx.key] = ctx.val_a  # WHY: record after-side value even if None


def diff_key_dict(  # WHY: dict-branch delegate keeps diff_key CC<=5
    key: str,
    val_b: dict[str, Any],
    val_a: dict[str, Any],
    delta_b: dict[str, Any],
    delta_a: dict[str, Any],
) -> None:
    """Recurse into nested dict values for ``key``."""
    sub_b, sub_a = compute_delta(val_b, val_a)  # WHY: reuse the top-level delta walker recursively
    if sub_b or sub_a:  # WHY: only record when the recursion found a change
        delta_b[key] = sub_b  # WHY: attach recursion result to before-side output
        delta_a[key] = sub_a  # WHY: attach recursion result to after-side output


def diff_key_list(  # WHY: list-branch delegate keeps diff_key CC<=5
    key: str,
    val_b: list[Any],
    val_a: list[Any],
    delta_b: dict[str, Any],
    delta_a: dict[str, Any],
) -> None:
    """Recurse into nested list values for ``key``."""
    list_b, list_a = compute_delta_list(val_b, val_a)  # WHY: identity-aware list diff
    if list_b is not None or list_a is not None:  # WHY: None sentinel means 'no change'
        delta_b[key] = list_b if list_b is not None else []  # WHY: substitute [] to keep JSON valid
        delta_a[key] = list_a if list_a is not None else []  # WHY: substitute [] to keep JSON valid


def compute_delta_list(  # WHY: exported list-diff entry point with identity fallback
    before: list[Any],
    after: list[Any],
) -> tuple[list[Any] | None, list[Any] | None]:
    """Extract delta for list values with identity-based dict matching."""
    if before == after:  # WHY: identical lists produce no delta at all
        return None, None  # WHY: None sentinel signals 'no delta' to caller
    all_dicts = _all_dicts(before) and _all_dicts(after)  # WHY: identity match only makes sense for dicts
    if not all_dicts:  # WHY: fall back to raw before/after for mixed types
        return before, after  # WHY: mixed types cannot share identity keys, so emit raw lists
    return delta_by_identity(before, after)  # WHY: dict-of-dicts path handles reorder/added/removed


def _all_dicts(items: list[Any]) -> bool:  # WHY: cheap type-uniformity gate for identity path
    """Return True when every element is a dict."""
    return all(isinstance(item, dict) for item in items)  # WHY: cheap type guard for identity path


def element_identity(element: dict[str, Any]) -> str | None:  # WHY: exported for tests via renderer facade
    """Return a stable identity string for a dict element or ``None``."""
    for key in _IDENTITY_KEYS:  # WHY: priority order controls collision resolution
        val = element.get(key)  # WHY: first non-None wins
        if val is not None:  # WHY: skip missing/explicit-null identity slots
            return f"{key}={val}"  # WHY: prefix key so 'name=foo' and 'id=foo' do not collide
    return None  # WHY: caller treats missing identity as anonymous element


def build_identity_map(  # WHY: exported for tests. Splits list into id-keyed + positional groups
    elements: list[dict[str, Any]],
) -> tuple[dict[str, dict[str, Any]], list[dict[str, Any]]]:
    """Split ``elements`` into identified and anonymous groups."""
    id_map: dict[str, dict[str, Any]] = {}  # WHY: identity string -> element for O(1) join
    anon: list[dict[str, Any]] = []  # WHY: collect unidentifiable elements for positional diff
    for elem in elements:  # WHY: single-pass classification keeps CC low
        eid = element_identity(elem)  # WHY: try each identity candidate in priority order
        if eid and eid not in id_map:  # WHY: first occurrence wins. Duplicates fall through to anon
            id_map[eid] = elem  # WHY: record identity-keyed element for O(1) later lookup
        else:
            anon.append(elem)  # WHY: unidentifiable/duplicate falls to positional diff bucket
    return id_map, anon  # WHY: caller uses tuple to drive identified + anon diff passes


def diff_identified(  # WHY: exported for tests. Runs identity-matched pair diff loop
    before_map: dict[str, dict[str, Any]],
    after_map: dict[str, dict[str, Any]],
    delta_b: list[dict[str, Any]],
    delta_a: list[dict[str, Any]],
) -> None:
    """Diff elements matched by identity, appending changes to deltas."""
    all_ids = list(dict.fromkeys(list(before_map) + list(after_map)))  # WHY: preserve first-seen order
    for eid in all_ids:  # WHY: iterate union of identities
        item_b = before_map.get(eid)  # WHY: may be None if only present in after
        item_a = after_map.get(eid)  # WHY: may be None if only present in before
        _apply_identity_pair(item_b, item_a, delta_b, delta_a)  # WHY: dispatch keeps this loop at CC<=5


def _apply_identity_pair(  # WHY: single-pair delta dispatcher keeps diff_identified CC<=5
    item_b: dict[str, Any] | None,
    item_a: dict[str, Any] | None,
    delta_b: list[dict[str, Any]],
    delta_a: list[dict[str, Any]],
) -> None:
    """Append the delta for a single identified before/after pair."""
    if item_b == item_a:  # WHY: unchanged pair contributes nothing
        return  # WHY: skip unchanged pairs to keep delta minimal
    if item_b is not None and item_a is not None:  # WHY: both present -> recurse to find sub-delta
        _append_pair_delta(item_b, item_a, delta_b, delta_a)  # WHY: matched pair delegated to nested walker
        return  # WHY: pair path consumed. Skip single-side branch
    _apply_single_side(item_b, item_a, delta_b, delta_a)  # WHY: exactly one side present branch


def _apply_single_side(  # WHY: emits added/removed markers when only one side present
    item_b: dict[str, Any] | None,
    item_a: dict[str, Any] | None,
    delta_b: list[dict[str, Any]],
    delta_a: list[dict[str, Any]],
) -> None:
    """Emit an added/removed marker when exactly one of the sides is present."""
    if item_b is not None:  # WHY: only before present -> element was removed
        delta_b.append(item_b)  # WHY: keep the removed element on the before side
        delta_a.append({"_status": "(removed)"})  # WHY: placeholder marker for the after side
        return  # WHY: exit before evaluating the added branch
    if item_a is not None:  # WHY: only after present -> element was added
        delta_b.append({"_status": "(added)"})  # WHY: placeholder marker for the before side
        delta_a.append(item_a)  # WHY: keep the added element on the after side


def _append_pair_delta(
    item_b: dict[str, Any],
    item_a: dict[str, Any],
    delta_b: list[dict[str, Any]],
    delta_a: list[dict[str, Any]],
) -> None:
    """Compute nested delta for a matched pair and append if non-empty."""
    sub_b, sub_a = compute_delta(item_b, item_a)  # WHY: nested change may not affect identity keys
    if sub_b or sub_a:  # WHY: only record when recursion produced content
        delta_b.append(sub_b)
        delta_a.append(sub_a)


def diff_anonymous(
    before_anon: list[dict[str, Any]],
    after_anon: list[dict[str, Any]],
    delta_b: list[dict[str, Any]],
    delta_a: list[dict[str, Any]],
) -> None:
    """Diff unidentified elements by position, appending changes to deltas."""
    min_len = min(len(before_anon), len(after_anon))  # WHY: overlap zone diffed by index
    for index in range(min_len):  # WHY: descriptive name replaces bare 'i' (CONV-NAME fix)
        _diff_anonymous_at(before_anon[index], after_anon[index], delta_b, delta_a)
    _append_tail_removed(before_anon[min_len:], delta_b, delta_a)  # WHY: extras on 'before' side removed
    _append_tail_added(after_anon[min_len:], delta_b, delta_a)  # WHY: extras on 'after' side added


def _diff_anonymous_at(
    item_b: dict[str, Any],
    item_a: dict[str, Any],
    delta_b: list[dict[str, Any]],
    delta_a: list[dict[str, Any]],
) -> None:
    """Diff a single positional pair inside the overlap zone."""
    if item_b == item_a:  # WHY: identical anonymous entries contribute nothing
        return
    sub_b, sub_a = compute_delta(item_b, item_a)  # WHY: nested walk in case dicts differ
    if sub_b or sub_a:  # WHY: only append when recursion produced content
        delta_b.append(sub_b)
        delta_a.append(sub_a)


def _append_tail_removed(
    tail: list[dict[str, Any]],
    delta_b: list[dict[str, Any]],
    delta_a: list[dict[str, Any]],
) -> None:
    """Append each tail element as a removed marker pair."""
    for item in tail:  # WHY: entries only present on the 'before' side
        delta_b.append(item)
        delta_a.append({"_status": "(removed)"})


def _append_tail_added(
    tail: list[dict[str, Any]],
    delta_b: list[dict[str, Any]],
    delta_a: list[dict[str, Any]],
) -> None:
    """Append each tail element as an added marker pair."""
    for item in tail:  # WHY: entries only present on the 'after' side
        delta_b.append({"_status": "(added)"})
        delta_a.append(item)


def check_reorder(
    before_map: dict[str, dict[str, Any]],
    after_map: dict[str, dict[str, Any]],
) -> tuple[list[dict[str, Any]] | None, list[dict[str, Any]] | None]:
    """Detect reordering when identity sets match but ordering differs."""
    before_ids = list(before_map.keys())  # WHY: preserve insertion order for comparison
    after_ids = list(after_map.keys())  # WHY: preserve insertion order for comparison
    if before_ids == after_ids or sorted(before_ids) != sorted(after_ids):  # WHY: no reorder to report
        return None, None
    label = reorder_label(before_ids)  # WHY: descriptive marker naming which identity fields reordered
    return (
        [{label: [strip_id_prefix(k) for k in before_ids]}],  # WHY: emit human-readable identity list
        [{label: [strip_id_prefix(k) for k in after_ids]}],
    )


def delta_by_identity(
    before: list[dict[str, Any]],
    after: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]] | None, list[dict[str, Any]] | None]:
    """Match list elements by best-available identity and diff."""
    before_map, before_anon = build_identity_map(before)  # WHY: split into identified + anonymous groups
    after_map, after_anon = build_identity_map(after)  # WHY: same split on the after side
    delta_b: list[dict[str, Any]] = []  # WHY: accumulator for the 'before' side of the delta
    delta_a: list[dict[str, Any]] = []  # WHY: accumulator for the 'after' side of the delta
    diff_identified(before_map, after_map, delta_b, delta_a)  # WHY: match by identity keys
    diff_anonymous(before_anon, after_anon, delta_b, delta_a)  # WHY: positional fallback for anon rows
    if not delta_b and not delta_a:  # WHY: fall back to reorder-only signal when values unchanged
        return check_reorder(before_map, after_map)
    return delta_b, delta_a


def reorder_label(identity_keys: list[str]) -> str:
    """Build a descriptive label from identity key prefixes."""
    prefixes = {k.split("=", 1)[0] for k in identity_keys if "=" in k}  # WHY: extract 'name' from 'name=x'
    fields = ", ".join(sorted(prefixes)) if prefixes else "index"  # WHY: deterministic label ordering
    return f"_reordered (by {fields})"  # WHY: leading underscore keeps label distinct from real keys


def strip_id_prefix(identity: str) -> str:
    """Strip the ``key=`` prefix from an identity string."""
    return identity.split("=", 1)[1] if "=" in identity else identity  # WHY: keep raw value for display
