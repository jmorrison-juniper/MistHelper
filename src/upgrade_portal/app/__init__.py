"""The web layer of the capture portal.

Why:
    This subpackage holds the application factory, the configuration, the
    security layer, the routes, and the assets. Each part belongs to the
    HTTP surface. The domain logic stays in the other subpackages, so a
    change to a route does not change the capture logic or the upgrade
    logic.
"""
