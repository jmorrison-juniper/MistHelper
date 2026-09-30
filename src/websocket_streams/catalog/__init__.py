"""The catalog of every Mist WebSocket stream that the portal can start.

Why:
    The server holds the catalog in one place. The page reads the catalog from
    the server, so the page never holds a channel path of its own.
"""
