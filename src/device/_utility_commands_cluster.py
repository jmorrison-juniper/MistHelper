"""Shared base class for :mod:`src.device.utility_commands` cluster wrappers.

Every ``_utility_commands_*`` sibling module (selection, websocket, show,
action, clear) wraps :class:`~src.device.utility_commands.DeviceUtilityCommands`
with an identical ``__init__`` + ``__getattr__`` proxy so its methods can
call sibling helpers as if they lived on the parent. Extracting the
boilerplate here removes ~14 lines of duplicated code per cluster and
keeps pylint's ``duplicate-code`` (R0801) warnings out of the score gate
while preserving the ``self._method(...)`` ergonomics the clusters rely
on.
"""

from __future__ import annotations  # WHY: postponed evaluation for forward-ref parent type

from typing import TYPE_CHECKING, Any  # WHY: Any lets __getattr__ proxy any parent method

if TYPE_CHECKING:  # WHY: only pulled in by type checkers; skipped at runtime
    from src.device.utility_commands import DeviceUtilityCommands  # WHY: parent type for annotation


class _ClusterBase:  # WHY: shared wrapper base for every utility_commands cluster
    """Base class holding the parent-proxy pattern used by every cluster.

    Concrete cluster classes bind the parent :class:`DeviceUtilityCommands`
    at construction time and inherit ``__getattr__`` so any attribute
    lookup that misses on the cluster falls through to the parent (which
    in turn dispatches to its other clusters via its own ``__getattr__``).
    """

    def __init__(self, parent: DeviceUtilityCommands) -> None:  # WHY: bind parent for delegated lookups
        """Store the parent :class:`DeviceUtilityCommands` for delegate lookups."""
        self._uc = parent  # WHY: enable __getattr__ delegation back to parent state

    def __getattr__(self, name: str) -> Any:  # WHY: proxy unknown attrs back to parent
        """Delegate unknown attributes to the wrapped parent object."""
        parent = self.__dict__.get("_uc")  # WHY: guard against half-initialized instances
        if parent is None:  # WHY: only trips during broken init; avoid infinite recursion
            raise AttributeError(name)  # WHY: signal missing attribute cleanly to callers
        return getattr(parent, name)  # WHY: transparent proxy so self._apisession / helpers work
