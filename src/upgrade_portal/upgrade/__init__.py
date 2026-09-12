"""The modules that drive the firmware upgrade and wait for the site to settle.

Why:
    The upgrade is a long operation with a strict order and a stop control.
    This subpackage holds the version options, the run state machine, the
    settle gate, the event polling, and the stop control. The capture code
    and the compare code then contain no upgrade timing rules.
"""
