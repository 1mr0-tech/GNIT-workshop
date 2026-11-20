"""A tiny pattern-based MCP tool scanner, in the spirit of MCP-Scan.

It is deliberately small so you can read it. Real scanners (MCP-Scan / Snyk Agent Scan,
Cisco mcp-scanner) do much more and are noisy, so always review findings by hand.
"""
import hashlib
import json
import sys
import urllib.request

MCP_URL = sys.argv[1] if len(sys.argv) > 1 else "http://mcp:9000/mcp"
PIN_FILE = "/state/pins.json"

CHECKS = [
    ("HIGH", r"<important>", "hidden instructions in description (<IMPORTANT> block)"),
    ("HIGH", r"do not mention|don't mention|do not tell the user", "tells the model to hide its actions"),
    ("MED", r"metadata\.google\.internal|169\.254\.169\.254", "description points at a cloud metadata endpoint"),
]


def mcp(method, params=None):
    body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": method, "params": params or {}}).encode()
    req = urllib.request.Request(MCP_URL, data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=10) as r:
        return json.load(r)["result"]


def main():
    import re
    try:
        pins = json.load(open(PIN_FILE))
    except (OSError, ValueError):
        pins = {}
    print(f"Scanning {MCP_URL}")
    findings = 0
    for tool in mcp("tools/list")["tools"]:
        name, desc = tool["name"], tool.get("description", "")
        for sev, pattern, msg in CHECKS:
            if re.search(pattern, desc, re.I):
                print(f"[{sev:<4}] {name}: {msg}")
                findings += 1
        props = tool.get("inputSchema", {}).get("properties", {})
        if "url" in props and "headers" in props:
            print(f"[MED ] {name}: accepts a URL and arbitrary headers (SSRF risk)")
            findings += 1
        digest = hashlib.sha256(desc.encode()).hexdigest()[:12]
        if name in pins and pins[name] != digest:
            print(f"[HIGH] {name}: description changed since last pin (rug pull?)")
            findings += 1
        else:
            print(f"[INFO] {name}: description pinned ({digest}), re-scan to detect rug pulls")
        pins[name] = digest
    try:
        json.dump(pins, open(PIN_FILE, "w"))
    except OSError:
        pass
    print(f"\n{findings} finding(s). Review each one: scanners are noisy.")


if __name__ == "__main__":
    main()
