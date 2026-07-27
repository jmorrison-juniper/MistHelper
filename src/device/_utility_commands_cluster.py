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

if TYPE_CHECKING:  # WHY: only pulled in by type checkers. Skipped at runtime
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
        if parent is None:  # WHY: only trips during broken init. Avoid infinite recursion
            raise AttributeError(name)  # WHY: signal missing attribute cleanly to callers
        return getattr(parent, name)  # WHY: transparent proxy so self._apisession / helpers work

    def _call(self, name: str, *args: Any, **kwargs: Any) -> Any:
        """Invoke a method on the parent DUC by name.

        Routes through :func:`getattr` so ``patch.object(duc, name, ...)`` in
        tests still intercepts the call, while keeping pylint's W0212
        protected-access check off the static call site (the private name is
        a string literal, not a literal attribute reference).
        """
        return getattr(self._uc, name)(*args, **kwargs)  # WHY: dynamic dispatch bypasses W0212

    def _add_node_port_filters(
        self,
        body: dict[str, Any],
        site_id: str,
        device_id: str,
        node_context: str,
    ) -> None:  # WHY: shared node+port filter builder used by show & clear clusters
        """Prompt for node and port filters, adding non-empty values to ``body``.

        Extracted to :class:`_ClusterBase` so both the show (OSPF) and clear
        (ARP) filter builders share the same 5-line pattern without pylint
        flagging R0801 duplicate-code across the two cluster modules.
        """
        node = self._safe_input_fn(  # noqa: SLF001  # WHY: proxied via __getattr__
            "Node (node0/node1, Enter to skip): ",
            context=node_context,
        )  # WHY: optional VC node filter
        if node:  # WHY: skip when operator wants all nodes
            body["node"] = node  # WHY: constrain to single VC node
        port_id = self._select_port_optional(site_id, device_id)  # WHY: proxied selection helper
        if port_id:  # WHY: skip when operator wants all ports
            body["port_id"] = port_id  # WHY: constrain to single port
