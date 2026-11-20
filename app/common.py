import json
import os

STATE_DIR = os.environ.get("LAB_STATE", "/state")
STATE_FILE = os.path.join(STATE_DIR, "defense.json")
BIND = os.environ.get("LAB_BIND", "0.0.0.0")
LAYERS = ("filter", "policy", "egress")

SHOPBOT_PORT = int(os.environ.get("SHOPBOT_PORT", "8080"))
MCP_PORT = int(os.environ.get("MCP_PORT", "9000"))
METADATA_PORT = int(os.environ.get("METADATA_PORT", "80"))

# Docker-free mode (python lab.py): map the lab's host names onto localhost.
if os.environ.get("LAB_LOCAL"):
    import localnet  # noqa: F401


def load_state():
    """Defense switches live in a shared file so changes take effect without a restart."""
    try:
        with open(STATE_FILE) as f:
            data = json.load(f)
    except (OSError, ValueError):
        data = {}
    return {k: bool(data.get(k)) for k in LAYERS}


def save_state(flags):
    os.makedirs(STATE_DIR, exist_ok=True)
    with open(STATE_FILE, "w") as f:
        json.dump({k: bool(flags.get(k)) for k in LAYERS}, f)
        f.write("\n")
