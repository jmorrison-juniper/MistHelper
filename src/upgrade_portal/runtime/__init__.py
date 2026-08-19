"""The shared services that every other subpackage uses.

Why:
    The identity registry, the site lock, the run records, the thread pools,
    and the stop signals apply to more than one stage of the operator
    journey. This subpackage holds them all, so no single stage owns a
    service that another stage also needs.
"""
