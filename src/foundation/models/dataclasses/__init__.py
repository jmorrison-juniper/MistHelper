"""Shared frozen dataclasses used to keep function signatures within the 5-Item Rule (max 5 params).

Each dataclass groups parameters that travel together across function calls so the calling
contract stays narrow without losing type information. All dataclasses in this package follow
the same conventions:

* ``@dataclass(frozen=True, slots=True)`` -- immutable so callers cannot mutate shared state.
* Maximum 5 fields per dataclass (the 5-Item Rule applies recursively).
* Field names mirror the original parameter names so the rename is a non-semantic substitution.

Issue: https://github.com/jmorrison-juniper/MistHelper/issues/431
"""
