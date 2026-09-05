"""The modules that read the state of a site and store it.

Why:
    The portal reads the site state one time before the upgrade and one
    time after the upgrade. This subpackage holds the readers, the document
    assembly, and the store. Both reads then follow the same code path and
    produce the same document shape.
"""
