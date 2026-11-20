"""Docker-free mode: make the lab's host names resolve to localhost.

In Docker, shopbot / mcp / metadata.google.internal are container names. Without Docker we
rewrite those (host, port) pairs to 127.0.0.1 at connection time, inside the lab's own
processes only. Nothing on your system (hosts file, DNS) is changed.
"""
import os
import socket
import urllib.request

_LOCAL = "127.0.0.1"
_MAP = {
    ("metadata.google.internal", 80): (_LOCAL, int(os.environ.get("METADATA_PORT", "8081"))),
    ("metadata", 80): (_LOCAL, int(os.environ.get("METADATA_PORT", "8081"))),
    ("shopbot", 8080): (_LOCAL, int(os.environ.get("SHOPBOT_PORT", "8080"))),
    ("mcp", 9000): (_LOCAL, int(os.environ.get("MCP_PORT", "9000"))),
}
_orig_create_connection = socket.create_connection


def _create_connection(address, *args, **kwargs):
    host, port = address
    key = (str(host).lower().rstrip("."), port)
    return _orig_create_connection(_MAP.get(key, address), *args, **kwargs)


socket.create_connection = _create_connection
# Ignore any system HTTP proxy so lab traffic never leaves the machine.
urllib.request.install_opener(urllib.request.build_opener(urllib.request.ProxyHandler({})))
