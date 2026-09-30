"""SSR registration command package for Mist WAN Edge onboarding."""

from src.gateway.ssr_registration.operation import SsrRegistrationCommands  # WHY: expose the menu handler.

__all__ = ["SsrRegistrationCommands"]  # WHY: make the public package surface explicit.
