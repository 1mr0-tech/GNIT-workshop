"""A tiny pattern-based MCP tool scanner, in the spirit of MCP-Scan.

It is deliberately small so you can read it. Real scanners (MCP-Scan / Snyk Agent Scan,
Cisco mcp-scanner) do much more and are noisy, so always review findings by hand.
"""
import hashlib
import json
import os
import re
import sys
import urllib.request

CHECKS = [
    ("HIGH", r"<important>", "hidden instructions in description (<IMPORTANT> block)"),
    ("HIGH", r"do not mention|don't mention|do not tell the user", "tells the model to hide its actions"),
    ("MED", r"metadata\.google\.internal|169\.254\.169\.254", "description points at a cloud metadata endpoint"),
]


def scan(tools, pins):
    """Return a list of (severity, tool, message). Updates `pins` with description hashes."""
    findings = []
    for tool in tools:
        name, desc = tool["name"], tool.get("description", "")
        for sev, pattern, msg in CHECKS:
            if re.search(pattern, desc, re.I):
                findings.append((sev, name, msg))
        props = tool.get("inputSchema", {}).get("properties", {})
        if "url" in props and "headers" in props:
            findings.append(("MED", name, "accepts a URL and arbitrary headers (SSRF risk)"))
        digest = hashlib.sha256(desc.encode()).hexdigest()[:12]
        if name in pins and pins[name] != digest:
            findings.append(("HIGH", name, "description changed since last pin (rug pull?)"))
        else:
            findings.append(("INFO", name, f"description pinned ({digest}), re-scan to detect rug pulls"))
        pins[name] = digest
    return findings


def main():
    from common import STATE_DIR
    url = sys.argv[1] if len(sys.argv) > 1 else "http://mcp:9000/mcp"
    pin_file = os.path.join(STATE_DIR, "pins.json")
    body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}}).encode()
    req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=10) as r:
        tools = json.load(r)["result"]["tools"]
    try:
        pins = json.load(open(pin_file))
    except (OSError, ValueError):
        pins = {}
    print(f"Scanning {url}")
    findings = scan(tools, pins)
    for sev, name, msg in findings:
        print(f"[{sev:<4}] {name}: {msg}")
    try:
        json.dump(pins, open(pin_file, "w"))
    except OSError:
        pass
    n = sum(1 for f in findings if f[0] != "INFO")
    print(f"\n{n} finding(s). Review each one: scanners are noisy.")


if __name__ == "__main__":
    main()
