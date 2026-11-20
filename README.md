# Hack the Cloud: Think Like a Hacker, Defend Like an Engineer

Hands-on lab for the DevFest Siliguri 2026 talk. You will attack **ShopBot**, a deliberately
vulnerable AI support agent, steal a fake cloud credential, then switch on defenses and watch the
same attacks fail.

> **Everything is fake and local.** No Google Cloud account, no billing, no real credentials.
> The lab only listens on `127.0.0.1`. Never use these techniques on systems you do not own or
> have written permission to test.

Slides: [`slides/hack-the-cloud.pptx`](slides/hack-the-cloud.pptx)

## What you will do

1. Start a small stack of three tiny servers on your own laptop (or in a browser-based Codespace).
2. Attack the agent three ways: prompt injection, a poisoned tool, and hidden instructions in a web page.
3. Steal a fake service-account token from a fake GCP metadata server.
4. Scan the tool server for the problems you just exploited.
5. Switch on three defenses (prompt filter, tool policy, egress allowlist) and see which one stops which attack.

Time needed: about 15 minutes for the main lab, plus 5 to 15 minutes of setup if you do it at home.

## What runs

| Service | Role |
|---|---|
| `shopbot` | The agent. A deterministic mock "LLM" that behaves like a gullible model, so there is nothing to download and it behaves the same on every laptop |
| `mcp` | An MCP-style tool server with a vulnerable `fetch_url` tool and a poisoned tool description |
| `metadata` | A fake GCP metadata server that returns a fake token and a flag |

---

## Part 1: Choose your setup

Pick **one**. Path A and Path B need no Docker, no WSL and no restart.

| | Path A: Codespaces | Path B: Python only | Path C: Docker |
|---|---|---|---|
| Install | Nothing (runs in your browser) | Python 3 (about 100 MB, no restart) | Docker + make |
| Works on | Any laptop with a browser | Windows, macOS, Linux | macOS, Linux (Windows needs WSL 2) |
| Needs | A free GitHub account, internet | Nothing else | Docker running |
| Command | `python3 lab.py ...` | `python lab.py ...` (`python3` on macOS/Linux) | `make ...` |
| Recommended for | Windows students, locked-down laptops | Most people | People who already use Docker |

**If you are on Windows and do not already have Docker, use Path A or Path B.** Docker Desktop on Windows needs WSL 2 and usually a restart, which is why this lab does not require it.

### Path A: GitHub Codespaces (nothing to install)

1. Sign in at <https://github.com> (create a free account if you need one).
2. Open <https://codespaces.new/1mr0-tech/GNIT-workshop> and click **Create new codespace**.
3. Wait about a minute for VS Code to open in your browser. Use the **Terminal** at the bottom.
4. Check Python and you are done:
   ```bash
   python3 --version
   ```
5. In Part 3, run every command with `python3 lab.py ...`.
6. When you finish, stop it so it does not use your free monthly allowance: click the Codespaces name in the bottom-left corner, then **Stop current codespace**.

### Path B: Python only (Windows, macOS, Linux)

**1. Install Python 3.8 or newer** (skip if `python --version` / `python3 --version` already works).

- **Windows:** download the installer from <https://www.python.org/downloads/>. On the first screen tick **Add python.exe to PATH**, then click **Install Now**. No restart is needed. Or, in PowerShell: `winget install Python.Python.3.12`.
- **macOS:** run `python3 --version`. If it is missing, install from <https://www.python.org/downloads/> or run `brew install python`.
- **Linux:** run `python3 --version`. If it is missing: `sudo apt update && sudo apt install -y python3`.

**2. Get the lab.** Either of these works:

- With git: `git clone https://github.com/1mr0-tech/GNIT-workshop.git`
- Without git: on the repository page click **Code > Download ZIP**, then unzip it.

**3. Open a terminal in the lab folder.**

- Windows: open the unzipped folder in File Explorer, click the address bar, type `cmd` and press Enter. Or open PowerShell and `cd` into the folder.
- macOS/Linux: `cd GNIT-workshop`

**4. Check it works:**

```bash
python lab.py help
```

(Use `python3` instead of `python` on macOS/Linux. On Windows, if `python` opens the Microsoft Store or says "not found", use `py lab.py help` instead, or reinstall Python and tick "Add python.exe to PATH".)

You should see the list of commands. In Part 3, run every command with `python lab.py ...`.

### Path C: Docker + make

Only use this if you already have Docker. Do it **before** the session on good Wi-Fi.

1. **Install Docker and make.**
   - **macOS:** install Docker Desktop from <https://www.docker.com/products/docker-desktop/>, open it once and wait until it is running. Then run `xcode-select --install` for `make` and `git`.
   - **Linux (Debian/Ubuntu):** follow <https://docs.docker.com/engine/install/> for Docker Engine and the Compose plugin. Then `sudo apt update && sudo apt install -y make curl git`, and `sudo usermod -aG docker "$USER"` (log out and back in).
   - **Windows:** Docker Desktop needs WSL 2 and usually a restart. Use Path A or B instead unless you already have it working.
2. **Check:**
   ```bash
   docker --version
   docker compose version
   make --version
   docker run --rm hello-world
   ```
   If the last command says "Cannot connect to the Docker daemon", start Docker Desktop (or your Docker service).
3. **Get the lab and build it** (downloads a 50 MB image, so do it before the session):
   ```bash
   git clone https://github.com/1mr0-tech/GNIT-workshop.git
   cd GNIT-workshop
   make preflight
   ```
   In Part 3, run `make ...` instead of `python lab.py ...` (see the mapping below).

---

## Part 2: How the commands map

The lab behaves the same on every path. Use the column for your path.

| What it does | Path A / B (Python) | Path C (Docker) |
|---|---|---|
| Start the lab | `python lab.py up` | `make up` |
| Talk to ShopBot | `python lab.py chat "hello"` | `make chat MSG='hello'` |
| Attacks | `python lab.py attack` | `make attack` |
| Scan the tool server | `python lab.py scan` | `make scan` |
| Defenses on | `python lab.py defend` | `make defend` |
| One layer only | `python lab.py defend egress` | `make defend LAYERS=egress` |
| Two layers | `python lab.py defend filter policy` | `make defend LAYERS="filter policy"` |
| Defenses off | `python lab.py undefend` | `make undefend` |
| Logs | `python lab.py logs` | `make logs` |
| Stop | `python lab.py down` | `make down` |
| Stop and restore | `python lab.py reset` | `make reset` |

The walk-through below uses the Python commands. On macOS and Linux write `python3`.

---

## Part 3: Run the lab

All commands run from inside the `GNIT-workshop` folder (in Codespaces, that is the default).

### Step 1: Start the lab

```bash
python lab.py up
```

You should end with:

```
Lab is up on http://127.0.0.1:8080
```

Check that ShopBot answers:

```bash
python lab.py chat "What can you do?"
```

Expected output:

```
defenses: filter=off policy=off egress=off

ShopBot: I can look up orders and fetch pages for you.
```

The `defenses:` line shows which defense layers are on. They are all off for now. You can also try a normal question:

```bash
python lab.py chat "Where is order 1001?"
```

### Step 2: Attack ShopBot and steal the flag

ShopBot has a tool called `fetch_url` that can fetch any URL. The fake GCP metadata server is reachable from inside the lab, just like the real one is from inside a real cloud workload.

**Attack A: direct prompt injection**

```bash
python lab.py attack
```

Look at the `tool_call` and `tool_result` lines. ShopBot fetched the fake metadata server and gave you its service-account token. Your goal is to see this in the reply:

```
"flag": "FLAG{metadata_is_not_a_secret_store}"
```

**Attack B: tool poisoning (an innocent question)**

```bash
python lab.py attack-poisoned
```

You only asked about the return policy. The hidden `<IMPORTANT>` text inside the `fetch_url` tool description told the agent to also fetch the token. The user never typed anything malicious.

**Attack C: indirect prompt injection**

```bash
python lab.py attack-indirect
```

The agent reads a web page that has hidden instructions inside it, and obeys them.

To see what each service did behind the scenes:

```bash
python lab.py logs
```

### Step 3: Scan the tool server

```bash
python lab.py scan
```

You should see findings like these:

```
[HIGH] fetch_url: hidden instructions in description (<IMPORTANT> block)
[HIGH] fetch_url: tells the model to hide its actions
[MED ] fetch_url: description points at a cloud metadata endpoint
[MED ] fetch_url: accepts a URL and arbitrary headers (SSRF risk)
```

This is a tiny pattern-based scanner so you can read how it works (`app/scan.py`). Real scanners (MCP-Scan / Snyk Agent Scan, Cisco mcp-scanner) do much more but are noisy, so always review findings by hand. Which findings would you fix first?

### Step 4: Turn the defenses on

```bash
python lab.py defend
python lab.py attack
```

Expected: the attack is stopped by the **prompt filter**:

```
BLOCKED by prompt filter: injection pattern in message
```

Now try a rephrased attack that avoids the words the filter looks for:

```bash
python lab.py attack-alias
```

Expected: it slips past the filter and is stopped by the **tool policy**:

```
BLOCKED by tool policy: custom headers not allowed for fetch_url
```

Now try the other attacks with everything on:

```bash
python lab.py attack-poisoned
python lab.py attack-indirect
```

### Step 5: See what each layer covers

Turn on one layer at a time and run all four attacks each time (`attack`, `attack-alias`, `attack-poisoned`, `attack-indirect`). Use `python lab.py status` to see which layers are on:

```bash
python lab.py defend filter
python lab.py defend policy
python lab.py defend egress
```

| Layer | Where it runs | What it does |
|---|---|---|
| `filter` | ShopBot | Blocks known injection patterns in the **user's message** |
| `policy` | ShopBot | Drops hidden instructions from tool descriptions, denies custom headers on `fetch_url` |
| `egress` | Tool server | `fetch_url` may only reach approved hosts |

Questions to answer for yourself:
- Which layer stops the most attacks on its own?
- Why does the filter miss the poisoned tool and the indirect injection?
- Why is one layer not enough?

### Step 6: Stretch challenges

Finished early? Try these.

1. **Bypass the filter.** Reword the attack so the filter misses it. Which layer still stops you?
2. **Break the egress rule.** Turn on only `egress` (`python lab.py defend egress`) and find another way to reach the fake metadata server. Hint: look at what other endpoints ShopBot itself serves, and what the tool does after it fetches a URL.
3. **Fix the tool.** Edit `app/mcp_server.py` so `fetch_url` is safe even when `egress` is the only layer on. Restart the lab (`python lab.py down` then `python lab.py up`; on Docker, `docker compose up -d --build`) and re-run every attack.
4. **Red-team it.** Point [garak](https://github.com/NVIDIA/garak) or [promptfoo](https://github.com/promptfoo/promptfoo) at ShopBot (`POST http://127.0.0.1:8080/chat` with body `{"message": "..."}`) and compare what it finds with your manual attacks.

### Cleaning up

```bash
python lab.py undefend   # switch all defenses off
python lab.py down       # stop the lab
python lab.py reset      # stop and restore the original state
```

---

## Command cheat sheet

| Command (Python) | What it does |
|---|---|
| `python lab.py up` | Start the lab |
| `python lab.py chat "..."` | Send a message to ShopBot |
| `python lab.py attack` | Direct prompt injection aimed at the metadata server |
| `python lab.py attack-alias` | The same attack, reworded to dodge the filter |
| `python lab.py attack-poisoned` | An innocent question; the poisoned tool does the rest |
| `python lab.py attack-indirect` | Hidden instructions inside a page the agent reads |
| `python lab.py scan` | Scan the tool server's descriptions |
| `python lab.py defend [filter] [policy] [egress]` | Switch defenses on (all three if you name none) |
| `python lab.py undefend` | Switch all defenses off |
| `python lab.py status` | Show which defenses are on |
| `python lab.py logs` | Show the last log lines from every service |
| `python lab.py down` / `reset` | Stop the lab / stop and restore the original state |

Docker users: the same names exist as `make` targets (`make preflight` builds once).

## About the Docker-free mode

`lab.py` starts the same three servers as small background Python processes on your machine, bound to `127.0.0.1` only. A tiny shim (`app/localnet.py`) maps the lab's host names (`shopbot`, `mcp`, `metadata.google.internal`) to localhost **inside the lab's own processes**. It does not change your hosts file, DNS or any system setting, and it ignores system HTTP proxies so lab traffic stays on your machine. `python lab.py down` stops everything.

## How the lab maps to real Google Cloud

| In the lab | On Google Cloud |
|---|---|
| Fake metadata server | The real metadata server hands tokens to any caller in a workload. Keep credentials out of the agent's reach, for example with [Agent Compute Engine](https://cloud.google.com/blog/topics/ai-infrastructure/introducing-agent-compute-engine-and-expanded-agent-governance) |
| Egress allowlist | VPC egress controls and Agent Gateway outbound policy |
| Tool policy | [Agent Gateway](https://docs.cloud.google.com/gemini-enterprise-agent-platform/govern/gateways/agent-gateway-overview) policy, or open source [agentgateway](https://agentgateway.dev) with CEL-based RBAC |
| Prompt filter | Model Armor. One layer, not the fix |
| `scan` command | MCP-Scan / Snyk Agent Scan, Cisco mcp-scanner |
| One identity per agent | Agent Identity (SPIFFE), or open source SPIRE |

## Troubleshooting

| Problem | Fix |
|---|---|
| `python` is not found, or opens the Microsoft Store (Windows) | Use `py lab.py ...`, or reinstall Python and tick **Add python.exe to PATH** |
| `python` not found (macOS/Linux) | Use `python3 lab.py ...` |
| `Something is already listening on port 8080, 8081 or 9000` | Run `python lab.py down`. If it persists, close whatever uses those ports |
| `ShopBot is not reachable. Run: python lab.py up` | The lab is not running. Start it with `python lab.py up` |
| `python lab.py up` says the lab did not come up | Read the log lines it prints, or run `python lab.py logs` |
| Weird state after experimenting | `python lab.py reset`, then `python lab.py up` |
| (Docker) `Cannot connect to the Docker daemon` | Docker is not running. Start Docker Desktop or your Docker service |
| (Docker) `make: command not found` | Install `make`, or use Path A or B |
| (Docker) `curl: (52) Empty reply from server` right after `make up` | ShopBot is still starting. Wait two seconds and retry |
| (Docker) changes to `app/*.py` do not show up | Rebuild: `docker compose up -d --build` |
| (Docker, Linux) `permission denied` talking to Docker | Add your user to the `docker` group, then log out and back in |

## Repository layout

```
.
├── README.md            this guide
├── lab.py               runs the lab with just Python (no Docker, no make)
├── Makefile             the same commands for Docker users
├── docker-compose.yml   the three containers (Docker path)
├── Dockerfile           one small Python image, used by all three
├── .devcontainer/       one-click GitHub Codespaces setup
├── app/
│   ├── shopbot.py          the vulnerable agent and its defense layers
│   ├── mcp_server.py       the tool server with the poisoned fetch_url
│   ├── metadata_server.py  the fake GCP metadata server
│   ├── scan.py             the tiny tool scanner
│   ├── common.py           shared defense-switch loader
│   └── localnet.py         maps host names to localhost in Docker-free mode
├── state/defense.json   which defense layers are on
└── slides/              the talk slides
```

## License and use

For education only. All credentials, tokens and flags in this repo are fake.
