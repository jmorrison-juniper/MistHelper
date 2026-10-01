"""Read the enum annotations of the Mist SDK utility functions.

Why:
    Issue #3551. The live check showed the routes utility with the traceroute
    protocol values. One SDK parameter name can use a different enum in each
    function. The catalog and the runner must read the enum from the SDK
    signature of the function, not from a shared name table.
"""

from __future__ import annotations  # Postponed annotations keep each hint import-safe.

import logging  # The portal uses standard logging for each action.
from collections.abc import Callable  # The SDK functions are plain callables.
from enum import Enum  # Some SDK parameters use an enum.
from typing import Any, get_args, get_origin, get_type_hints  # Read the real SDK annotations.

logger = logging.getLogger(__name__)  # Keep annotation log records under this module name.


class SdkAnnotation:
    """Read the parameter annotations of one SDK function."""

    @staticmethod
    def hints(function: Callable[..., Any]) -> dict[str, object]:
        """Return the resolved annotations of one SDK function.

        Args:
            function: The SDK facade function.

        Returns:
            The annotations by parameter name. The result is empty when the
            SDK names a type that Python cannot resolve.
        """
        logger.debug("Reading the SDK annotations of %s", getattr(function, "__name__", "function"))  # Debug level.
        try:  # The SDK shell functions name a type that the module does not import.
            return dict(get_type_hints(function))  # Resolve the text annotations to real types.
        except (NameError, TypeError) as error:  # An unresolved name gives no enum information.
            logger.debug("The SDK annotations are not readable: %s", error)  # Record the reason at debug level.
            return {}  # A function without readable annotations takes plain values.

    @staticmethod
    def enum_type(annotation: object) -> type[Enum] | None:
        """Return the enum type inside one annotation.

        Args:
            annotation: The type annotation to inspect.

        Returns:
            The enum class, or None.
        """
        if isinstance(annotation, type) and issubclass(annotation, Enum):  # Direct enum annotation.
            return annotation  # The caller can construct it from a value.
        for option in get_args(annotation) if get_origin(annotation) is not None else ():  # Unwrap an optional type.
            if isinstance(option, type) and issubclass(option, Enum):  # Find the enum inside the union.
                return option  # The caller can construct it from a value.
        return None  # No enum conversion applies.

    @classmethod
    def enum_choices(cls, annotation: object) -> tuple[str, ...]:
        """Return the text values of the enum inside one annotation.

        Args:
            annotation: The type annotation to inspect.

        Returns:
            The enum values in SDK order, or an empty tuple.
        """
        enum_class = cls.enum_type(annotation)  # Find the enum, if the annotation holds one.
        if enum_class is None:  # A plain annotation has no fixed values.
            return ()  # The caller uses its own choice table.
        return tuple(str(member.value) for member in enum_class)  # Keep the SDK order for the page.
