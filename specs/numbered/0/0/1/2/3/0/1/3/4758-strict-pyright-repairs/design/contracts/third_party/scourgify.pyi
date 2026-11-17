"""Declare the documented address-normalization interface used by MistHelper."""

from collections.abc import Callable, Sequence

def normalize_address_record(
    address: str | dict[str, str | None],
    addr_map: dict[str, str] | None = None,
    addtl_funcs: Sequence[Callable[[str], tuple[str, str]]] | None = None,
    strict: bool = True,
    long_hand: bool = False,
) -> dict[str, str | None]: ...
