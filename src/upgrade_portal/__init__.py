"""The browser application that captures the state of a site around a firmware upgrade.

Why:
    An operator must prove that a firmware upgrade changes nothing except
    the firmware version. This package captures the state of a site before the
    upgrade. It captures the state again after the upgrade, and it reports
    every difference between the two captures.
"""
