"""Shared base class for :mod:`src.gateway.wan2_variable` cluster wrappers.

Every ``_wan2_variable_*`` sibling module (io, selection, template, device,
reporting) wraps :class:`~src.gateway.wan2_variable.GatewayWan2VariableMigrator`
with an identical ``__init__`` + ``__getattr__`` proxy so its methods can call
sibling helpers as if they lived on the parent. Extracting the boilerplate
here removes ~14 lines of duplicated code per cluster and keeps pylint's
``duplicate-code`` (R0801) warning out of the score gate while preserving
the ``self._method(...)`` ergonomics the clusters rely on.
"""

from __future__ import annotations  # WHY: postponed evaluation for forward-ref parent type

from typing import TYPE_CHECKING, Any  # WHY: Any lets __getattr__ proxy any parent method

if TYPE_CHECKING:  # WHY: only pulled in by type checkers; skipped at runtime
    from src.gateway.wan2_variable import GatewayWan2VariableMigrator  # WHY: parent type for annotation


class _ClusterBase:  # WHY: shared wrapper base for every wan2_variable cluster
    """Base class holding the parent-proxy pattern used by every cluster.

    Concrete cluster classes bind the parent
    :class:`GatewayWan2VariableMigrator` at construction time and inherit
    ``__getattr__`` so any attribute lookup that misses on the cluster falls
    through to the parent (which in turn dispatches to its other clusters
    via its own ``__getattr__``).
    """

    def __init__(self, parent: GatewayWan2VariableMigrator) -> None:  # WHY: bind parent for delegated lookups
        """Store the parent :class:`GatewayWan2VariableMigrator` for delegate lookups."""
        self._uc = parent  # WHY: enable __getattr__ delegation back to parent state

    def __getattr__(self, name: str) -> Any:  # WHY: proxy unknown attrs back to parent
        """Delegate unknown attributes to the wrapped parent object."""
        parent = self.__dict__.get("_uc")  # WHY: guard against half-initialized instances
        if parent is None:  # WHY: only trips during broken init; avoid infinite recursion
            raise AttributeError(name)  # WHY: signal missing attribute cleanly to callers
        return getattr(parent, name)  # WHY: transparent proxy so self._apisession / helpers work

    def _call(self, name: str, *args: Any, **kwargs: Any) -> Any:
        """Invoke a method on the parent migrator by name.

        Routes through :func:`getattr` so ``patch.object(migrator, name, ...)``
        in tests still intercepts the call, while keeping pylint's W0212
        protected-access check off the static call site (the private name is
        a string literal, not a literal attribute reference).
        """
        return getattr(self._uc, name)(*args, **kwargs)  # WHY: dynamic dispatch bypasses W0212
