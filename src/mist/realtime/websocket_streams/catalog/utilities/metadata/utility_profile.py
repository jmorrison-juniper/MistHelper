"""Classify utility safety, output, and scope."""

from src.mist.realtime.websocket_streams.catalog.model import Safety  # Use the public utility safety classes.


class UtilityProfile:
    """Return the established behavior profile for one utility."""

    def safety(self, name: str) -> Safety:
        """Return the utility safety class."""
        if name == "createShellSession":  # Shell sessions give device command access.
            return Safety.SHELL  # Require the shell enabling flag.
        if "Pcap" in name:  # Remote packet captures collect device traffic.
            return Safety.CAPTURE  # Use capture handling and packet output.
        changes = {"releaseDhcpLeases", "bouncePort", "cableTest", "clearSessions"}  # Name disruptive actions.
        return Safety.CHANGE if name in changes else Safety.READ  # Preserve the reviewed safety classification.

    def output(self, name: str, safety: Safety) -> str:
        """Return the page output view."""
        if safety is Safety.SHELL:  # A shell needs interactive terminal output.
            return "terminal"  # Preserve the terminal page view.
        if safety is Safety.CAPTURE:  # A capture sends packet records.
            return "packets"  # Preserve the packet page view.
        return "screen" if name in {"topCommand", "monitorTraffic"} else "lines"  # Preserve text view behavior.

    def scope(self, family: str, name: str) -> str:
        """Return the identifier scope for one utility."""
        if family == "mxedge" and name == "orgRemotePcap":  # One Mist Edge capture is organization scoped.
            return "organization"  # Preserve the organization start request.
        return "site"  # Every other utility starts in a site.
