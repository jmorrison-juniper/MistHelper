"""Menu 270 -- export the Marvis Actions of one organization, and resolve them in bulk.

Why:
    The package splits the feature into five modules. ``model`` names the
    topics and builds the flat rows. ``client`` makes every Mist API call.
    ``selection`` reads the filter answers and asks the prompts. ``alarms``
    joins each exported action to its Marvis alarm. ``operation`` runs the
    menu option for the SSH menu, the command line, and the web dashboard.
    The web dashboard reads its filter lists from the catalogs in ``model``,
    so the portal choices and the CLI tables use the same keys.
"""

from src.marvis.actions.operation import MarvisActionsOperation  # WHY: the menu row calls its run method.

__all__ = ["MarvisActionsOperation"]  # WHY: declare the public entry point of the package.
