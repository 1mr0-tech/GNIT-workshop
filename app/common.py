import json

STATE_FILE = "/state/defense.json"
LAYERS = ("filter", "policy", "egress")


def load_state():
    """Defense switches live in a shared file so `make defend` takes effect without a restart."""
    try:
        with open(STATE_FILE) as f:
            data = json.load(f)
    except (OSError, ValueError):
        data = {}
    return {k: bool(data.get(k)) for k in LAYERS}
