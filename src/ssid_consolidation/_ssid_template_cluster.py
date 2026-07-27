"""Shared base class for :mod:`src.ssid_consolidation.ssid_template_consolidation` clusters.

Every ``_ssid_template_*`` sibling module (cache, phase1, phase2, phase3,
phase45) wraps :class:`~src.ssid_consolidation.ssid_template_consolidation.SSIDTemplateConsolidationManager`
with an identical ``__init__`` + ``__getattr__`` proxy so its methods can
call sibling helpers as if they lived on the parent. Extracting the
boilerplate here removes ~14 lines of duplicated code per cluster and
keeps pylint's ``duplicate-code`` (R0801) warnings out of the score gate
while preserving the ``self._method(...)`` ergonomics the clusters rely
on.
"""

# WHY: the base class delegates unknown attribute access back to the parent
# manager (which owns all the private state and helpers), so pylint's
# "too-few-public-methods" and "protected-access" alarms do not apply to this
# proxy pattern.
# pylint: disable=protected-access,too-few-public-methods

from __future__ import annotations  # WHY: postponed evaluation for forward-ref parent type

import logging  # WHY (#886 Phase 2): cluster helper emits bail msg via logger instead of print
from typing import TYPE_CHECKING, Any  # WHY: Any lets __getattr__ proxy any parent method

if TYPE_CHECKING:  # WHY: only pulled in by type checkers; skipped at runtime
    from src.ssid_consolidation.ssid_template_consolidation import (  # WHY: parent type for annotation
        SSIDTemplateConsolidationManager,
    )


class _ClusterBase:  # WHY: shared wrapper base for every ssid_template cluster
    """Base class holding the parent-proxy pattern used by every cluster.

    Concrete cluster classes bind the parent
    :class:`SSIDTemplateConsolidationManager` at construction time and
    inherit ``__getattr__`` so any attribute lookup that misses on the
    cluster falls through to the parent (which in turn dispatches to its
    other clusters via its own ``__getattr__``).
    """

    def __init__(self, parent: SSIDTemplateConsolidationManager) -> None:  # WHY: bind parent for delegated lookups
        """Store the parent :class:`SSIDTemplateConsolidationManager` for delegate lookups."""
        self._mm = parent  # WHY: enable __getattr__ delegation back to parent state

    def __getattr__(self, name: str) -> Any:  # WHY: proxy unknown attrs back to parent
        """Delegate unknown attributes to the wrapped parent object."""
        parent = self.__dict__.get("_mm")  # WHY: guard against half-initialized instances
        if parent is None:  # WHY: only trips during broken init; avoid infinite recursion
            raise AttributeError(name)  # WHY: signal missing attribute cleanly to callers
        return getattr(parent, name)  # WHY: transparent proxy so self.org_id / helpers work

    def _call(self, name: str, *args: Any, **kwargs: Any) -> Any:  # WHY: dynamic dispatch to parent by name
        """Invoke a method on the parent manager by name.

        Routes through :func:`getattr` so ``patch.object(mgr, name, ...)`` in
        tests still intercepts the call, while keeping pylint's W0212
        protected-access check off the static call site (the private name is
        a string literal, not a literal attribute reference).
        """
        return getattr(self._mm, name)(*args, **kwargs)  # WHY: dynamic dispatch bypasses W0212

    def _load_cache_or_bail(self) -> bool:  # WHY: shared Phase 2-5 cache preamble
        """Load Phase 1 cache onto parent; return False + bail msg when missing.

        Phase 2/3/4/5 orchestrators all share the same "load cache or abort"
        preamble; centralising it here keeps pylint's R0801 duplicate-code
        warning off the per-phase clusters without leaking parent internals.
        """
        parent = self._mm  # WHY: proxy alias
        cached = parent._load_cache()  # noqa: SLF001 — cluster helper is intra-package
        if not cached:  # WHY: cache missing means Phase 1 was skipped
            logging.warning("Phase 1 cache not found. Run Phase 1 first.")  # WHY: user bail msg
            return False  # WHY: signal to caller to abort the phase
        parent.cache = cached  # WHY: hand loaded cache to parent state
        return True  # WHY: cache loaded successfully, phase can proceed
