import json
import os

STATE_DIR = os.environ.get("LAB_STATE", "/state")
STATE_FILE = os.path.join(STATE_DIR, "defense.json")
BIND = os.environ.get("LAB_BIND", "0.0.0.0")
LAYERS = ("filter", "policy", "egress")

# Docker-free mode (python lab.py): map the lab's host names onto localhost.
if os.environ.get("LAB_LOCAL"):
    import localnet  # noqa: F401


def load_state():
    """Defense switches live in a shared file so `make defend` takes effect without a restart."""
    try:
        with open(STATE_FILE) as f:
            data = json.load(f)
    except (OSError, ValueError):
        data = {}
    return {k: bool(data.get(k)) for k in LAYERS}
