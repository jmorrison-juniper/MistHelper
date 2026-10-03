"""The engine and the page of the WebSockets tab in the Operations portal.

Why:
    Issue #3551. The Mist API streams live data on WebSocket channels, and a
    device utility sends its output on a WebSocket channel. The Operations
    portal hid every WebSocket menu, so an operator had to use the Mist
    dashboard. This package lists every stream that the mistapi SDK gives,
    checks each start request, holds each live connection in the server, and
    serves the page that shows the messages.
"""
