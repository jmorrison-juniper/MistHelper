"""The shared services that every other subpackage uses.

Why:
    The identity registry, the site lock, the run records, the thread pools,
    and the stop signals serve more than one stage of the journey. This
    subpackage holds them all. No single stage then owns a service that
    another stage also needs.
"""
